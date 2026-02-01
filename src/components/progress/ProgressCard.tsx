'use client'

/**
 * 学习进度卡片组件
 *
 * 显示章节学习进度，包括：
 * - 进度条（带颜色编码和动画）
 * - 对话轮数、学习时长
 * - 掌握程度等级
 * - 学习建议
 */

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { MessageSquare, Clock, Award, TrendingUp, Loader2 } from 'lucide-react'
import { getApiUrl, getAuthHeadersSimple } from '@/lib/config'

interface ProgressData {
  completion_percentage: number
  dialogue_rounds: number
  study_time_minutes: number
  quiz_attempts: number
  quiz_success_rate: number
  mastery_level: string
  mastery_text: string
  recommendations: string[]
  last_activity: string | null
}

interface ProgressCardProps {
  userId: number
  documentId: number
  chapterNumber: number
}

export function ProgressCard({ userId, documentId, chapterNumber }: ProgressCardProps) {
  const [progress, setProgress] = useState<ProgressData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchProgress()
  }, [userId, documentId, chapterNumber])

  const fetchProgress = async () => {
    try {
      setLoading(true)
      const response = await fetch(
        getApiUrl(`/api/teaching/progress-analysis?user_id=${userId}&document_id=${documentId}&chapter_number=${chapterNumber}`),
        {
          headers: getAuthHeadersSimple()
        }
      )

      if (response.ok) {
        const data = await response.json()
        setProgress(data)
      } else {
        setError('加载进度失败')
      }
    } catch (err) {
      console.error('加载进度失败:', err)
      setError('加载进度失败')
    } finally {
      setLoading(false)
    }
  }

  // 获取进度条颜色
  const getProgressColor = (percentage: number) => {
    if (percentage < 30) return 'bg-red-500'
    if (percentage < 70) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  // 获取掌握等级图标和颜色
  const getMasteryStyle = (level: string) => {
    const styles = {
      novice: { color: 'text-gray-600', bg: 'bg-gray-100', icon: '🌱' },
      beginner: { color: 'text-blue-600', bg: 'bg-blue-100', icon: '📚' },
      intermediate: { color: 'text-yellow-600', bg: 'bg-yellow-100', icon: '⭐' },
      proficient: { color: 'text-green-600', bg: 'bg-green-100', icon: '🎯' },
      advanced: { color: 'text-purple-600', bg: 'bg-purple-100', icon: '👑' }
    }
    return styles[level as keyof typeof styles] || styles.novice
  }

  if (loading) {
    return (
      <div className="p-6 bg-white rounded-2xl border border-gray-200">
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
        </div>
      </div>
    )
  }

  if (error || !progress) {
    return (
      <div className="p-6 bg-white rounded-2xl border border-gray-200">
        <p className="text-center text-gray-500">{error || '暂无进度数据'}</p>
      </div>
    )
  }

  const masteryStyle = getMasteryStyle(progress.mastery_level)

  return (
    <div className="p-6 bg-white rounded-2xl border border-gray-200 hover:shadow-lg transition-shadow">
      {/* 标题 */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-black">学习进度</h3>
        <div className={`px-3 py-1 rounded-full ${masteryStyle.bg} ${masteryStyle.color} flex items-center gap-1`}>
          <span>{masteryStyle.icon}</span>
          <span className="text-sm font-medium">{progress.mastery_text}</span>
        </div>
      </div>

      {/* 进度条 */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-600">完成度</span>
          <span className="text-sm font-semibold text-black">{progress.completion_percentage}%</span>
        </div>
        <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
          <motion.div
            className={`h-full ${getProgressColor(progress.completion_percentage)} rounded-full`}
            initial={{ width: 0 }}
            animate={{ width: `${progress.completion_percentage}%` }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
          />
        </div>
      </div>

      {/* 学习统计 */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {/* 对话轮数 */}
        <div className="text-center p-3 bg-gray-50 rounded-xl">
          <MessageSquare className="w-5 h-5 mx-auto mb-1 text-black" />
          <div className="text-lg font-semibold text-black">{progress.dialogue_rounds}</div>
          <div className="text-xs text-gray-500">对话轮数</div>
        </div>

        {/* 学习时长 */}
        <div className="text-center p-3 bg-gray-50 rounded-xl">
          <Clock className="w-5 h-5 mx-auto mb-1 text-black" />
          <div className="text-lg font-semibold text-black">{progress.study_time_minutes}</div>
          <div className="text-xs text-gray-500">学习分钟</div>
        </div>

        {/* 测试表现 */}
        {progress.quiz_attempts > 0 && (
          <div className="text-center p-3 bg-gray-50 rounded-xl">
            <Award className="w-5 h-5 mx-auto mb-1 text-black" />
            <div className="text-lg font-semibold text-black">{Math.round(progress.quiz_success_rate)}%</div>
            <div className="text-xs text-gray-500">正确率</div>
          </div>
        )}
      </div>

      {/* 学习建议 */}
      {progress.recommendations.length > 0 && (
        <div className="border-t border-gray-100 pt-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-black" />
            <span className="text-sm font-medium text-black">学习建议</span>
          </div>
          <ul className="space-y-1">
            {progress.recommendations.map((rec, index) => (
              <li key={index} className="text-sm text-gray-600 flex items-start gap-2">
                <span className="text-black mt-0.5">•</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
