'use client'

/**
 * Mistakes Page - 错题本页面
 * 展示所有错题，支持重做和查看解析
 */

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { AlertCircle, RefreshCw, CheckCircle2, TrendingUp, Filter } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { MistakeCard } from '@/components/mistakes'
import { safeFetch } from '@/lib/errors'
import { getApiUrl } from '@/lib/config'

interface Mistake {
  id: number
  question_id: number
  question_text: string
  options?: string
  user_answer: string
  correct_answer: string
  explanation?: string
  is_correct: boolean
  competency_dimension?: string
  difficulty: number
  chapter_number: number
  chapter_title?: string
  is_mastered: boolean
  attempts_count: number
  created_at: string
}

interface MistakeStats {
  total_mistakes: number
  mastered_mistakes: number
  mistakes_by_dimension: Record<string, number>
  mastery_rate: number
}

export default function MistakesPage() {
  const { user, token, isAuthenticated } = useAuth()
  const [mistakes, setMistakes] = useState<Mistake[]>([])
  const [stats, setStats] = useState<MistakeStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('all')

  // 加载错题数据
  useEffect(() => {
    if (!isAuthenticated || !user.id) {
      setLoading(false)
      return
    }

    loadMistakes()
    loadStats()
  }, [user.id, isAuthenticated, token])

  const loadMistakes = async () => {
    try {
      const response = await safeFetch(getApiUrl('/api/mistakes'), {
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        }
      })

      if (response.ok) {
        const data = await response.json()
        setMistakes(data.mistakes)
      }
    } catch (error) {
      console.error('加载错题失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const response = await safeFetch(getApiUrl('/api/mistakes/stats'), {
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        }
      })

      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch (error) {
      console.error('加载统计失败:', error)
    }
  }

  const handleMarkMastered = async (questionId: number) => {
    try {
      await safeFetch(getApiUrl(`/api/mistakes/${questionId}/mark-mastered`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
        body: JSON.stringify({ is_mastered: true })
      })

      // 重新加载数据
      await loadMistakes()
      await loadStats()
    } catch (error) {
      console.error('标记掌握失败:', error)
    }
  }

  const handlePractice = (questionId: number) => {
    // TODO: 实现专项练习模式
    console.log('开始练习题目:', questionId)
  }

  const handleFilterChange = async (dimension: string) => {
    setFilter(dimension)
    // TODO: 调用筛选API
  }

  // 如果用户未登录，显示提示
  if (!isAuthenticated || !user.id) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-semibold mb-4">错题本</h1>
          <p className="text-gray-500 mb-6">请先登录以查看您的错题</p>
          <a
            href="/login"
            className="px-6 py-3 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors"
          >
            前往登录
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-200 px-8 py-6">
        <div className="max-w-6xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
                <AlertCircle className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <h1 className="text-3xl font-semibold">错题本</h1>
                <p className="text-sm text-gray-500 mt-1">
                  记录学习过程中的错误，及时复习巩固
                </p>
              </div>
            </div>
            <button
              onClick={() => { loadMistakes(); loadStats() }}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="刷新"
            >
              <RefreshCw className="w-5 h-5 text-gray-600" />
            </button>
          </div>
        </div>
      </header>

      {/* Stats Overview */}
      <section className="px-8 py-6 border-b border-gray-200">
        <div className="max-w-6xl">
          {stats ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-6 bg-red-50 border border-red-200 rounded-2xl"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-red-700">错题总数</p>
                    <p className="text-3xl font-semibold text-red-900 mt-2">{stats.total_mistakes}</p>
                  </div>
                  <AlertCircle className="w-12 h-12 text-red-300" />
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="p-6 bg-orange-50 border border-orange-200 rounded-2xl"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-orange-700">待巩固</p>
                    <p className="text-3xl font-semibold text-orange-900 mt-2">{stats.total_mistakes - stats.mastered_mistakes}</p>
                  </div>
                  <TrendingUp className="w-12 h-12 text-orange-300" />
                </div>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="p-6 bg-green-50 border border-green-200 rounded-2xl"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-green-700">已掌握</p>
                    <p className="text-3xl font-semibold text-green-900 mt-2">{stats.mastered_mistakes}</p>
                  </div>
                  <CheckCircle2 className="w-12 h-12 text-green-300" />
                </div>
              </motion.div>
            </div>
          ) : (
            <div className="h-32 flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-black"></div>
            </div>
          )}
        </div>
      </section>

      {/* Filter Bar */}
      <section className="px-8 py-4 border-b border-gray-200">
        <div className="max-w-6xl flex items-center gap-4">
          <span className="text-sm font-medium text-gray-700">筛选：</span>
          <div className="flex gap-2">
            <button
              onClick={() => handleFilterChange('all')}
              className={`px-4 py-2 text-sm rounded-lg transition-colors ${
                filter === 'all'
                  ? 'bg-black text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              全部
            </button>
            <button
              onClick={() => handleFilterChange('comprehension')}
              className={`px-4 py-2 text-sm rounded-lg transition-colors ${
                filter === 'comprehension'
                  ? 'bg-black text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              理解力
            </button>
            <button
              onClick={() => handleFilterChange('logic')}
              className={`px-4 py-2 text-sm rounded-lg transition-colors ${
                filter === 'logic'
                  ? 'bg-black text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              逻辑
            </button>
            <button
              onClick={() => handleFilterChange('application')}
              className={`px-4 py-2 text-sm rounded-lg transition-colors ${
                filter === 'application'
                  ? 'bg-black text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              应用
            </button>
          </div>
          <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <Filter className="w-5 h-5 text-gray-600" />
          </button>
        </div>
      </section>

      {/* Mistakes List */}
      <section className="px-8 py-8">
        <div className="max-w-6xl">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-black"></div>
            </div>
          ) : mistakes.length === 0 ? (
            <div className="text-center py-20">
              <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle2 className="w-10 h-10 text-green-500" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">太棒了！</h2>
              <p className="text-gray-500">目前没有错题，继续保持！</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {mistakes.map((mistake, index) => (
                <MistakeCard
                  key={mistake.id}
                  question={{
                    id: mistake.question_id,
                    question_text: mistake.question_text,
                    options: mistake.options ? JSON.parse(mistake.options) : undefined,
                    correct_answer: mistake.correct_answer,
                    explanation: mistake.explanation,
                    user_answer: mistake.user_answer,
                    competency_dimension: mistake.competency_dimension,
                    difficulty: mistake.difficulty,
                    chapter_number: mistake.chapter_number,
                    chapter_title: mistake.chapter_title,
                    mistake_count: mistake.attempts_count
                  }}
                  is_mastered={mistake.is_mastered}
                  onMarkMastered={handleMarkMastered}
                  onPractice={handlePractice}
                />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Floating Action Button */}
      {mistakes.length > 0 && (
        <div className="fixed bottom-8 right-8">
          <motion.button
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => {
              // TODO: 开始专项练习
              console.log('开始专项练习')
            }}
            className="p-4 bg-black text-white rounded-full shadow-lg hover:bg-gray-800 transition-colors"
            title="开始专项练习"
          >
            <TrendingUp className="w-6 h-6" />
          </motion.button>
        </div>
      )}
    </div>
  )
}
