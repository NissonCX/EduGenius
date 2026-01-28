'use client'

/**
 * StudySidebar - 学习页面侧边栏
 * 展示 Level 勋章图标和核心考点卡片
 */

import { motion } from 'framer-motion'
import { Target, BookOpen, Lightbulb, Award, CheckCircle2 } from 'lucide-react'

interface StudySidebarProps {
  studentLevel: number
  chapterTitle: string
  keyPoints: string[]
  completedTopics: string[]
  className?: string
}

// Level 勋章配置
const LEVEL_BADGES = {
  1: { icon: '🌱', label: 'L1 基础', color: 'from-emerald-400 to-emerald-600', bgColor: 'bg-emerald-50' },
  2: { icon: '📗', label: 'L2 入门', color: 'from-blue-400 to-blue-600', bgColor: 'bg-blue-50' },
  3: { icon: '📘', label: 'L3 进阶', color: 'from-purple-400 to-purple-600', bgColor: 'bg-purple-50' },
  4: { icon: '📙', label: 'L4 高级', color: 'from-orange-400 to-orange-600', bgColor: 'bg-orange-50' },
  5: { icon: '🏆', label: 'L5 专家', color: 'from-red-400 to-red-600', bgColor: 'bg-red-50' }
}

export function StudySidebar({
  studentLevel,
  chapterTitle,
  keyPoints = [],
  completedTopics = [],
  className = ''
}: StudySidebarProps) {
  const badge = LEVEL_BADGES[studentLevel as keyof typeof LEVEL_BADGES] || LEVEL_BADGES[3]

  return (
    <div className={`w-80 bg-white border-l border-gray-200 flex flex-col ${className}`}>
      {/* Level 勋章 */}
      <div className="p-6 border-b border-gray-200">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className={`p-6 rounded-2xl bg-gradient-to-br ${badge.color} text-white text-center`}
        >
          <div className="text-4xl mb-2">{badge.icon}</div>
          <h3 className="font-semibold text-lg">{badge.label}</h3>
          <p className="text-sm opacity-90 mt-1">当前认知等级</p>
        </motion.div>

        {/* 等级进度 */}
        <div className="mt-4">
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-gray-600">升级进度</span>
            <span className="font-medium text-gray-900">72%</span>
          </div>
          <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-emerald-400 to-emerald-600 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: '72%' }}
              transition={{ duration: 0.8, ease: 'easeOut' }}
            />
          </div>
        </div>
      </div>

      {/* 核心考点卡片 */}
      <div className="flex-1 overflow-y-auto p-6">
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Target className="w-5 h-5 text-emerald-600" />
          核心考点
        </h3>

        <div className="space-y-3">
          {keyPoints.map((point, index) => {
            const isCompleted = completedTopics.includes(point)
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className={`p-3 rounded-xl border transition-all ${
                  isCompleted
                    ? 'bg-emerald-50 border-emerald-200'
                    : 'bg-white border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                    isCompleted ? 'bg-emerald-500' : 'bg-gray-100'
                  }`}>
                    {isCompleted ? (
                      <CheckCircle2 className="w-4 h-4 text-white" />
                    ) : (
                      <div className="w-2 h-2 rounded-full bg-gray-400" />
                    )}
                  </div>
                  <div className="flex-1">
                    <p className={`text-sm ${isCompleted ? 'text-emerald-900 line-through' : 'text-gray-900'}`}>
                      {point}
                    </p>
                    {isCompleted && (
                      <p className="text-xs text-emerald-600 mt-1">已完成</p>
                    )}
                  </div>
                </div>
              </motion.div>
            )
          })}
        </div>

        {/* 学习提示 */}
        <div className={`mt-6 p-4 rounded-xl ${badge.bgColor} border border-gray-200`}>
          <div className="flex items-start gap-3">
            <Lightbulb className={`w-5 h-5 ${badge.color.split(' ')[0].replace('from-', 'text-')} flex-shrink-0 mt-0.5`} />
            <div>
              <h4 className="font-medium text-sm text-gray-900 mb-1">学习建议</h4>
              <p className="text-xs text-gray-600">
                {studentLevel <= 2
                  ? '建议先理解基础概念，多做练习巩固。遇到困难随时向我提问。'
                  : studentLevel === 3
                  ? '可以尝试深入理解原理，探索知识之间的联系。'
                  : '尝试挑战更复杂的问题，培养批判性思维。'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 章节信息 */}
      <div className="p-6 border-t border-gray-200">
        <div className="flex items-center gap-3 text-sm">
          <BookOpen className="w-5 h-5 text-gray-400" />
          <div>
            <p className="text-gray-500">当前章节</p>
            <p className="font-medium text-gray-900">{chapterTitle}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
