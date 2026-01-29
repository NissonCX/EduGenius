'use client'

/**
 * StudySidebar - 学习页面右侧边栏
 * 极简黑白美学风格，展示导师风格和核心考点
 */

import { motion } from 'framer-motion'
import { Target, BookOpen, Lightbulb, CheckCircle2, Settings } from 'lucide-react'

interface StudySidebarProps {
  teachingStyle: number
  chapterTitle: string
  keyPoints: string[]
  completedTopics: string[]
  documentTitle?: string
  onBackToChapters?: () => void
  className?: string
}

// 导师风格配置
const TEACHING_STYLES = {
  1: { label: 'L1 温柔', description: '耐心细致，循序渐进', hint: '用简单的例子帮助你理解' },
  2: { label: 'L2 耐心', description: '详细讲解，注重基础', hint: '提供清晰的步骤指导' },
  3: { label: 'L3 标准', description: '平衡严谨，注重应用', hint: '既讲原理又重实践' },
  4: { label: 'L4 严格', description: '注重细节，深入理解', hint: '要求理解每一步推理' },
  5: { label: 'L5 严厉', description: '挑战思维，独立解决', hint: '培养批判性思维' }
}

export function StudySidebar({
  teachingStyle,
  chapterTitle,
  keyPoints = [],
  completedTopics = [],
  documentTitle,
  onBackToChapters,
  className = ''
}: StudySidebarProps) {
  const style = TEACHING_STYLES[teachingStyle as keyof typeof TEACHING_STYLES] || TEACHING_STYLES[3]

  return (
    <div className={`w-80 bg-white border-l border-gray-200 flex flex-col ${className}`}>
      {/* 文档和章节信息 */}
      {documentTitle && (
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-start gap-3 mb-4">
            <BookOpen className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <p className="text-xs text-gray-500 mb-1">当前教材</p>
              <p className="font-medium text-sm text-black line-clamp-2 mb-3">{documentTitle}</p>
              <p className="text-xs text-gray-500 mb-1">当前章节</p>
              <p className="font-medium text-sm text-black line-clamp-2">{chapterTitle}</p>
            </div>
          </div>
          {onBackToChapters && (
            <button
              onClick={onBackToChapters}
              className="w-full px-4 py-2 text-sm text-gray-600 hover:text-black border border-gray-200 rounded-lg hover:border-black transition-colors"
            >
              返回章节列表
            </button>
          )}
        </div>
      )}

      {/* 导师风格卡片 - 极简黑白设计 */}
      <div className="p-6 border-b border-gray-200">
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="p-6 rounded-2xl bg-black text-white"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Settings className="w-5 h-5" />
              <span className="text-sm font-medium opacity-80">当前风格</span>
            </div>
            <div className="px-3 py-1 bg-white/10 rounded-lg">
              <span className="text-sm font-semibold">{style.label}</span>
            </div>
          </div>

          <p className="text-sm opacity-90 leading-relaxed">{style.description}</p>

          <div className="mt-4 pt-4 border-t border-white/20">
            <p className="text-xs opacity-70 flex items-center gap-2">
              <Lightbulb className="w-3.5 h-3.5" />
              {style.hint}
            </p>
          </div>
        </motion.div>

        {/* 学习统计 - 极简设计 */}
        {keyPoints.length > 0 && (
          <div className="mt-4 space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">已完成</span>
              <span className="font-medium text-black">
                {completedTopics.length}/{keyPoints.length}
              </span>
            </div>
            <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-black rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${(completedTopics.length / keyPoints.length) * 100}%` }}
                transition={{ duration: 0.8, ease: 'easeOut' }}
              />
            </div>
          </div>
        )}
      </div>

      {/* 核心考点卡片 */}
      <div className="flex-1 overflow-y-auto p-6">
        <h3 className="font-semibold text-black mb-4 flex items-center gap-2">
          <Target className="w-5 h-5" />
          核心考点
        </h3>

        {keyPoints.length === 0 ? (
          <div className="text-center py-8 text-gray-400 text-sm">
            <Lightbulb className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>开始学习后将显示核心考点</p>
          </div>
        ) : (
          <div className="space-y-2">
            {keyPoints.map((point, index) => {
              const isCompleted = completedTopics.includes(point)
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.03 }}
                  className={`p-3 rounded-xl border transition-all ${
                    isCompleted
                      ? 'bg-gray-50 border-gray-300'
                      : 'bg-white border-gray-200 hover:border-gray-300 hover:shadow-sm'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                      isCompleted ? 'bg-black' : 'bg-gray-200'
                    }`}>
                      {isCompleted ? (
                        <CheckCircle2 className="w-3 h-3 text-white" />
                      ) : (
                        <div className="w-1.5 h-1.5 rounded-full bg-gray-400" />
                      )}
                    </div>
                    <div className="flex-1">
                      <p className={`text-sm leading-relaxed ${
                        isCompleted ? 'text-gray-500 line-through' : 'text-gray-900'
                      }`}>
                        {point}
                      </p>
                    </div>
                  </div>
                </motion.div>
              )
            })}
          </div>
        )}

        {/* 学习提示 - 极简设计 */}
        <div className="mt-6 p-4 rounded-xl bg-gray-50 border border-gray-200">
          <div className="flex items-start gap-3">
            <Lightbulb className="w-5 h-5 text-black flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-medium text-sm text-black mb-1">学习提示</h4>
              <p className="text-xs text-gray-600 leading-relaxed">
                {teachingStyle <= 2
                  ? '建议先理解基础概念，多做练习巩固。遇到困难随时向我提问。'
                  : teachingStyle === 3
                  ? '可以尝试深入理解原理，探索知识之间的联系。'
                  : '尝试挑战更复杂的问题，培养批判性思维。'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
