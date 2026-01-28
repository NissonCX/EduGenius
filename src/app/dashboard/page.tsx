'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { CompetencyRadar } from '@/components/charts/CompetencyRadar'
import { KnowledgeConstellation } from '@/components/charts/KnowledgeConstellation'
import { fetchCompetencyData, fetchKnowledgeGraph } from '@/lib/api'

export default function DashboardPage() {
  const [studentLevel, setStudentLevel] = useState(3)
  const [competencyData, setCompetencyData] = useState<any>(null)
  const [knowledgeGraph, setKnowledgeGraph] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true)
      try {
        // 模拟用户和文档 ID
        const userId = 1
        const documentId = 1

        // 并行获取数据
        const [competency, graph] = await Promise.all([
          fetchCompetencyData(userId, documentId),
          fetchKnowledgeGraph(userId, documentId, 1)
        ])

        setCompetencyData(competency)
        setKnowledgeGraph(graph)
      } catch (error) {
        console.error('Error loading dashboard data:', error)
      } finally {
        setIsLoading(false)
      }
    }

    loadData()
  }, [])

  const handleNodeClick = (node: any) => {
    console.log('Clicked node:', node)
    // 可以在这里添加导航到具体章节的逻辑
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <section className="container-x py-8 border-b border-gray-200">
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <h1 className="text-3xl font-semibold text-balance">学习仪表盘</h1>
          <p className="text-gray-500 mt-2">
            实时可视化你的学习进度和能力评估
          </p>
        </motion.div>
      </section>

      {/* Level Selector */}
      <section className="container-x py-6">
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-gray-700">当前认知等级：</span>
          <div className="flex gap-2">
            {[1, 2, 3, 4, 5].map((level) => (
              <button
                key={level}
                onClick={() => setStudentLevel(level)}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                  studentLevel === level
                    ? 'bg-black text-white shadow-md'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                L{level}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Visualization Grid */}
      {isLoading ? (
        <section className="container-x py-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {[1, 2].map((i) => (
              <div
                key={i}
                className="h-96 bg-gray-50 rounded-2xl border border-gray-200 flex items-center justify-center"
              >
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-black"></div>
              </div>
            ))}
          </div>
        </section>
      ) : (
        <section className="container-x py-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Competency Radar */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3 }}
              className="p-6 bg-white border border-gray-200 rounded-2xl shadow-sm hover:shadow-md transition-shadow duration-200"
            >
              <CompetencyRadar
                data={competencyData}
                studentLevel={studentLevel}
              />
            </motion.div>

            {/* Knowledge Constellation */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3, delay: 0.1 }}
              className="p-6 bg-white border border-gray-200 rounded-2xl shadow-sm hover:shadow-md transition-shadow duration-200"
            >
              <KnowledgeConstellation
                nodes={knowledgeGraph?.nodes}
                links={knowledgeGraph?.links}
                onNodeClick={handleNodeClick}
                height={400}
              />
            </motion.div>
          </div>
        </section>
      )}

      {/* Stats Overview */}
      <section className="container-x py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
        >
          <h2 className="text-xl font-semibold mb-6">学习统计</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[
              { label: '总学习时长', value: '12.5h', change: '+2.3h', trend: 'up' },
              { label: '完成章节', value: '8/12', change: '+2', trend: 'up' },
              { label: '平均正确率', value: '78%', change: '+5%', trend: 'up' },
              { label: '知识点掌握', value: '65%', change: '+8%', trend: 'up' }
            ].map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.1 * index }}
                className="p-4 bg-gray-50 rounded-xl border border-gray-200 hover:shadow-sm transition-shadow duration-200"
              >
                <p className="text-sm text-gray-600">{stat.label}</p>
                <p className="text-2xl font-semibold text-black mt-2">{stat.value}</p>
                <p className={`text-xs mt-2 ${stat.trend === 'up' ? 'text-emerald-600' : 'text-red-600'}`}>
                  {stat.change} 本周
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
          <div className="space-y-3">
            {[
              { action: '完成了', target: '第三章：矩阵运算', time: '10分钟前', status: 'completed' },
              { action: '开始了学习', target: '第四章：特征值与特征向量', time: '25分钟前', status: 'progress' },
              { action: '通过了测试', target: '第二章评估', time: '1小时前', status: 'success' },
              { action: '升级到', target: 'L3 进阶等级', time: '昨天', status: 'level-up' }
            ].map((activity, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.2, delay: 0.05 * index }}
                className="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-xl hover:shadow-sm transition-shadow duration-200"
              >
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${
                    activity.status === 'completed' ? 'bg-emerald-500' :
                    activity.status === 'progress' ? 'bg-blue-500' :
                    activity.status === 'success' ? 'bg-emerald-500' :
                    'bg-purple-500'
                  }`} />
                  <div>
                    <p className="text-sm text-black">
                      {activity.action} <span className="font-medium">{activity.target}</span>
                    </p>
                    <p className="text-xs text-gray-500 mt-1">{activity.time}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </section>
    </div>
  )
}
