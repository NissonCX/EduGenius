'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { CompetencyRadar } from '@/components/charts/CompetencyRadar'
import { KnowledgeConstellation } from '@/components/charts/KnowledgeConstellation'
import { StudyCalendar, StudyCurve } from '@/components/progress'
import { useAuth } from '@/contexts/AuthContext'
import { getApiUrl } from '@/lib/config'

export default function DashboardPage() {
  const router = useRouter()
  const { user, isAuthenticated, isLoading: authLoading, token } = useAuth()
  const [competencyData, setCompetencyData] = useState<any>(null)
  const [knowledgeGraph, setKnowledgeGraph] = useState<any>(null)
  const [isDataLoading, setIsDataLoading] = useState(true)  // 重命名避免冲突
  const [userStats, setUserStats] = useState<any>(null)
  const [mistakeStats, setMistakeStats] = useState<any>(null)
  const [availableDocuments, setAvailableDocuments] = useState<any[]>([])
  const [selectedDocumentId, setSelectedDocumentId] = useState<number | null>(null)
  const [recentActivities, setRecentActivities] = useState<any[]>([])
  const [studyDays, setStudyDays] = useState<any[]>([])
  const [studyCurveData, setStudyCurveData] = useState<any[]>([])

  // 获取用户当前风格（从后端获取，不可修改）
  const teachingStyle = user?.teachingStyle || 3

  useEffect(() => {
    const loadData = async () => {
      // 🔧 FIX: 检查认证加载状态，避免在加载期间错误返回
      if (authLoading || isAuthenticated === false || !user.id) {
        setIsDataLoading(false)
        return
      }

      setIsDataLoading(true)
      try {
        // 获取可用文档列表
        const docs = await fetchAvailableDocuments(token || undefined)
        setAvailableDocuments(docs)

        // 获取用户最近学习的进度记录
        const recentProgress = await fetchRecentProgress(user.id, token || undefined)

        // 确定要显示的文档ID
        let documentId = selectedDocumentId
        if (!documentId && docs.length > 0) {
          // 如果没有选中文档，使用最近学习的文档
          documentId = recentProgress?.document_id || docs[0].id
          setSelectedDocumentId(documentId)
        }

        if (!documentId) {
          setIsDataLoading(false)
          return
        }

        // 并行获取数据
        const [competency, graph, stats, mistakes, activities, calendarData, curveData] = await Promise.all([
          fetchCompetencyData(user.id, documentId, token || undefined),
          fetchKnowledgeGraph(user.id, documentId, 1, token || undefined),
          fetchUserStats(user.id, token || undefined),
          fetchMistakeStats(token || undefined),
          fetchRecentActivities(user.id, token || undefined),
          fetchStudyCalendar(user.id, token || undefined),
          fetchStudyCurve(user.id, token || undefined)
        ])

        setCompetencyData(competency)
        setKnowledgeGraph(graph)
        setUserStats(stats)
        setMistakeStats(mistakes)
        setRecentActivities(activities)
        setStudyDays(calendarData)
        setStudyCurveData(curveData)

        // 🔍 调试日志
        console.log('📊 学习日历数据:', calendarData)
        console.log('📈 学习曲线数据:', curveData)
        console.log('📅 学习日历条目数:', calendarData?.length || 0)
        console.log('📉 学习曲线条目数:', curveData?.length || 0)
      } catch (error) {
        console.error('Error loading dashboard data:', error)
      } finally {
        setIsDataLoading(false)
      }
    }

    loadData()
  }, [user.id, isAuthenticated, authLoading, selectedDocumentId])

  // 当用户选择不同文档时
  const handleDocumentChange = (docId: number) => {
    setSelectedDocumentId(docId)
  }

  // 获取可用文档列表
  const fetchAvailableDocuments = async (token?: string) => {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(
        getApiUrl('/api/documents'),
        { headers }
      )

      if (response.ok) {
        const data = await response.json()
        return data.documents || []
      }
    } catch (error) {
      console.error('Error fetching documents:', error)
    }
    return []
  }

  // 获取用户最近学习的进度记录
  const fetchRecentProgress = async (userId: number, token?: string) => {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(
        getApiUrl(`/api/users/${userId}/progress`),
        { headers }
      )

      if (response.ok) {
        const progress = await response.json()
        // 返回最近访问的进度记录
        if (progress && progress.length > 0) {
          return progress.sort((a: any, b: any) =>
            new Date(b.last_accessed_at || 0).getTime() - new Date(a.last_accessed_at || 0).getTime()
          )[0]
        }
      }
    } catch (error) {
      console.error('Error fetching recent progress:', error)
    }
    return null
  }

  // 获取用户统计数据
  const fetchUserStats = async (userId: number, token?: string) => {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(
        getApiUrl(`/api/users/${userId}/stats`),
        { headers }
      )

      if (response.ok) {
        return await response.json()
      }
    } catch (error) {
      console.error('Error fetching user stats:', error)
    }
    return null
  }

  // 获取错题统计数据
  const fetchMistakeStats = async (token?: string) => {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(
        getApiUrl('/api/mistakes/stats'),
        { headers }
      )

      if (response.ok) {
        return await response.json()
      }
    } catch (error) {
      console.error('Error fetching mistake stats:', error)
    }
    return null
  }

  // 获取能力评估数据
  const fetchCompetencyData = async (userId: number, documentId: number, token?: string) => {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(
        getApiUrl(`/api/users/${userId}/history`),
        { headers }
      )

      if (response.ok) {
        const data = await response.json()
        return data.competency_scores || null
      }
    } catch (error) {
      console.error('Error fetching competency data:', error)
    }
    return null
  }

  // 获取知识图谱数据（从真实 API 获取）
  const fetchKnowledgeGraph = async (userId: number, documentId: number, chapter: number, token?: string) => {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(
        getApiUrl(`/api/knowledge/graph/${documentId}?user_id=${userId}`),
        { headers }
      )

      if (response.ok) {
        const data = await response.json()
        return data
      } else {
        console.warn('知识图谱 API 暂未返回数据，使用默认值')
        // 返回默认数据作为降级处理
        return {
          nodes: [],
          links: [],
          metadata: { document_id: documentId, user_id: userId, stats: {} }
        }
      }
    } catch (error) {
      console.error('获取知识图谱失败:', error)
      return {
        nodes: [],
        links: [],
        metadata: { document_id: documentId, user_id: userId, stats: {} }
      }
    }
  }

  // 获取最近活动
  const fetchRecentActivities = async (userId: number, token?: string) => {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(
        getApiUrl(`/api/users/${userId}/activities?limit=10`),
        { headers }
      )

      if (response.ok) {
        const data = await response.json()
        return data.activities || []
      } else {
        console.warn('获取活动历史失败，返回空数组')
        return []
      }
    } catch (error) {
      console.error('获取活动历史失败:', error)
      return []
    }
  }

  // 获取学习日历数据
  const fetchStudyCalendar = async (userId: number, token?: string) => {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(
        getApiUrl(`/api/users/${userId}/study-calendar?weeks=12`),
        { headers }
      )

      if (response.ok) {
        const data = await response.json()
        return data.study_days || []
      } else {
        console.warn('获取学习日历失败，返回空数组')
        return []
      }
    } catch (error) {
      console.error('获取学习日历失败:', error)
      return []
    }
  }

  // 获取学习曲线数据
  const fetchStudyCurve = async (userId: number, token?: string) => {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(
        getApiUrl(`/api/users/${userId}/study-curve?days=30`),
        { headers }
      )

      if (response.ok) {
        const data = await response.json()
        return data.data_points || []
      } else {
        console.warn('获取学习曲线失败，返回空数组')
        return []
      }
    } catch (error) {
      console.error('获取学习曲线失败:', error)
      return []
    }
  }

  const handleNodeClick = (node: any) => {
    console.log('Clicked node:', node)
    // 可以在这里添加导航到具体章节的逻辑
  }

  // 🔧 FIX: 只在明确不在加载中且未认证时显示登录提示
  if (!authLoading && isAuthenticated === false) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-semibold mb-4">学习仪表盘</h1>
          <p className="text-gray-500 mb-6">请先登录以查看您的学习数据</p>
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
      <section className="container-x py-4 sm:py-6 lg:py-8 border-b border-gray-200">
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <h1 className="text-2xl sm:text-3xl font-semibold text-balance">学习仪表盘</h1>
          <p className="text-gray-500 mt-1 sm:mt-2 text-sm sm:text-base">
            实时可视化你的学习进度和能力评估
          </p>
        </motion.div>
      </section>

      {/* Current Level Display */}
      <section className="container-x py-4 sm:py-6">
        <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4">
          <span className="text-sm font-medium text-gray-700">你的导师风格：</span>
          <div className="px-4 sm:px-6 py-2 bg-black text-white rounded-xl text-sm font-medium shadow-md w-fit">
            L{teachingStyle}
          </div>
          <span className="text-xs text-gray-500">
            {teachingStyle === 1 && '温柔 - 耐心细致，用简单的例子和鼓励帮助你理解'}
            {teachingStyle === 2 && '耐心 - 循序渐进，提供详细的讲解和指导'}
            {teachingStyle === 3 && '标准 - 平衡严谨，既讲清原理又注重应用'}
            {teachingStyle === 4 && '严格 - 注重细节，要求深入理解每一步推理'}
            {teachingStyle === 5 && '严厉 - 挑战思维，培养独立解决问题的能力'}
          </span>
        </div>
        <p className="text-xs text-gray-400 mt-2">
          💡 学习时可以临时调整风格，不会改变你的偏好设置
        </p>
      </section>

      {/* Document Selector */}
      {availableDocuments.length > 0 && (
        <section className="container-x py-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-gray-700">查看文档：</span>
            <select
              value={selectedDocumentId || ''}
              onChange={(e) => handleDocumentChange(Number(e.target.value))}
              className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-black"
            >
              {availableDocuments.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  {doc.title}
                </option>
              ))}
            </select>
          </div>
        </section>
      )}

      {/* Visualization Grid */}
      {isDataLoading || authLoading ? (
        <section className="container-x py-4 sm:py-6 lg:py-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
            {[1, 2].map((i) => (
              <div
                key={i}
                className="h-64 sm:h-80 lg:h-96 bg-gray-50 rounded-2xl border border-gray-200 flex items-center justify-center"
              >
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-black"></div>
              </div>
            ))}
          </div>
        </section>
      ) : (
        <section className="container-x py-4 sm:py-6 lg:py-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
            {/* Competency Radar */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3 }}
              className="p-4 sm:p-6 bg-white border border-gray-200 rounded-2xl shadow-sm hover:shadow-md transition-shadow duration-200"
            >
              <CompetencyRadar
                data={competencyData}
              />
            </motion.div>

            {/* Knowledge Constellation */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3, delay: 0.1 }}
              className="p-4 sm:p-6 bg-white border border-gray-200 rounded-2xl shadow-sm hover:shadow-md transition-shadow duration-200"
            >
              <KnowledgeConstellation
                nodes={knowledgeGraph?.nodes}
                links={knowledgeGraph?.links}
                onNodeClick={handleNodeClick}
                height={300}
              />
            </motion.div>
          </div>
        </section>
      )}

      {/* Progress Tracking */}
      <section className="container-x py-4 sm:py-6 lg:py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.15 }}
        >
          <h2 className="text-lg sm:text-xl font-semibold mb-4 sm:mb-6">学习进度追踪</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
            {/* 学习日历热力图 */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3 }}
              className="p-4 sm:p-6 bg-white border border-gray-200 rounded-2xl shadow-sm hover:shadow-md transition-shadow duration-200"
            >
              <StudyCalendar studyDays={studyDays} weeks={12} />
            </motion.div>

            {/* 学习曲线 */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3, delay: 0.1 }}
              className="p-4 sm:p-6 bg-white border border-gray-200 rounded-2xl shadow-sm hover:shadow-md transition-shadow duration-200"
            >
              <StudyCurve data={studyCurveData} />
            </motion.div>
          </div>
        </motion.div>
      </section>

      {/* Stats Overview */}
      <section className="container-x py-4 sm:py-6 lg:py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
        >
          <h2 className="text-lg sm:text-xl font-semibold mb-4 sm:mb-6">学习统计</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
            {[
              {
                label: '完成章节',
                value: userStats
                  ? `${userStats.total_chapters_completed}/${userStats.total_chapters || 0}`
                  : '-',
                change: userStats ? `${userStats.chapter_counts?.completed || 0} 已完成` : '-',
                trend: 'up' as const
              },
              {
                label: '总体进度',
                value: userStats ? `${Math.round(userStats.overall_progress_percentage)}%` : '-',
                change: '当前进度',
                trend: 'up' as const
              },
              {
                label: '学习文档',
                value: userStats ? `${userStats.total_documents_studied || 0}` : '-',
                change: '个文档',
                trend: 'up' as const
              },
              {
                label: '错题总数',
                value: mistakeStats?.total_mistakes ?? '-',
                change: mistakeStats ? `${mistakeStats.mastered_mistakes}/${mistakeStats.total_mistakes} 已掌握` : '-',
                href: '/mistakes',
                trend: 'down' as const,
                accent: 'red' as const
              }
            ].map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.1 * index }}
                className={`p-3 sm:p-4 rounded-xl border hover:shadow-sm transition-shadow duration-200 ${
                  stat.accent === 'red'
                    ? 'bg-red-50 border-red-200 hover:shadow-md cursor-pointer'
                    : 'bg-gray-50 border-gray-200'
                }`}
                onClick={() => stat.href && router.push(stat.href)}
              >
                <p className={`text-sm ${stat.accent === 'red' ? 'text-red-700' : 'text-gray-600'}`}>{stat.label}</p>
                <p className={`text-2xl font-semibold mt-2 ${stat.accent === 'red' ? 'text-red-900' : 'text-black'}`}>
                  {stat.value}
                </p>
                <p className={`text-xs mt-2 ${stat.accent === 'red' ? 'text-red-600' : 'text-gray-500'}`}>
                  {stat.change}
                </p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* Recent Activity */}
      <section className="container-x py-8 pb-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.3 }}
        >
          <h2 className="text-xl font-semibold mb-6">最近活动</h2>
          {isDataLoading || authLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-16 bg-gray-50 rounded-xl border border-gray-200 animate-pulse"
                />
              ))}
            </div>
          ) : recentActivities.length === 0 ? (
            <div className="text-center py-12 bg-white border border-gray-200 rounded-xl">
              <p className="text-gray-500">还没有学习活动记录，开始学习吧！</p>
            </div>
          ) : (
            <div className="space-y-3">
              {recentActivities.map((activity, index) => (
                <motion.div
                  key={activity.id || index}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.2, delay: 0.05 * index }}
                  className="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-xl hover:shadow-sm transition-shadow duration-200"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${
                      activity.status === 'completed' ? 'bg-black' :
                      activity.status === 'progress' ? 'bg-gray-400' :
                      activity.status === 'success' ? 'bg-black' :
                      activity.status === 'level-up' ? 'bg-gray-600' :
                      'bg-gray-400'
                    }`} />
                    <div>
                      <p className="text-sm text-black">
                        {activity.action} <span className="font-medium">{activity.target}</span>
                      </p>
                      {activity.document_title && (
                        <p className="text-xs text-gray-400 mt-0.5">{activity.document_title}</p>
                      )}
                      <p className="text-xs text-gray-500 mt-1">{activity.time}</p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </motion.div>
      </section>
    </div>
  )
}
