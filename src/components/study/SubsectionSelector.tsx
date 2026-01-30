'use client'

/**
 * SubsectionSelector - 小节选择器组件
 *
 * 功能：
 * - 面包屑导航显示当前学习位置
 * - 下拉选择器切换小节
 * - Glassmorphism 风格
 * - 平滑过渡动画
 */

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, Loader2 } from 'lucide-react'
import { getApiUrl, getAuthHeadersSimple, fetchWithTimeout } from '@/lib/config'

interface Subsection {
  subsection_number: string
  subsection_title: string
  page_number?: number
  completion_percentage: number
  time_spent_minutes: number
}

interface SubsectionSelectorProps {
  documentId: number
  chapterId: number
  chapterTitle: string
  currentSubsection?: string
  onSubsectionChange: (subsection: Subsection | null) => void
  disabled?: boolean
}

export function SubsectionSelector({
  documentId,
  chapterId,
  chapterTitle,
  currentSubsection,
  onSubsectionChange,
  disabled = false
}: SubsectionSelectorProps) {
  const [subsections, setSubsections] = useState<Subsection[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(false)

  // 加载小节列表
  useEffect(() => {
    const loadSubsections = async () => {
      setIsLoading(true)
      try {
        console.log(`[SubsectionSelector] 加载小节: document=${documentId}, chapter=${chapterId}`)
        const response = await fetchWithTimeout(
          getApiUrl(`/api/documents/${documentId}/chapters/${chapterId}/subsections`),
          {
            method: 'GET',
            headers: getAuthHeadersSimple()
          }
        )

        console.log(`[SubsectionSelector] 响应状态:`, response.status)

        if (response.ok) {
          const data = await response.json()
          console.log(`[SubsectionSelector] 返回数据:`, data)
          setSubsections(data.subsections || [])
        } else {
          console.error(`[SubsectionSelector] API 错误:`, response.status, response.statusText)
        }
      } catch (error) {
        console.error('[SubsectionSelector] 加载小节失败:', error)
      } finally {
        setIsLoading(false)
      }
    }

    if (documentId && chapterId) {
      loadSubsections()
    }
  }, [documentId, chapterId])

  // 当前选中的小节
  const currentSub = subsections.find(s => s.subsection_number === currentSubsection)

  const handleSubsectionSelect = (subsection: Subsection) => {
    onSubsectionChange(subsection)
    setIsOpen(false)
  }

  const handleBreadcrumbClick = () => {
    console.log('[SubsectionSelector] 点击选择器, disabled=', disabled, 'subsections.length=', subsections.length)
    if (!disabled) {
      setIsOpen(!isOpen)
    }
  }

  return (
    <div className="relative">
      {/* 面包屑导航栏 */}
      <div
        onClick={handleBreadcrumbClick}
        className={`flex items-center gap-2 px-4 py-2.5 rounded-2xl cursor-pointer transition-all duration-200 ${disabled ? 'bg-gray-100 cursor-not-allowed opacity-60' : 'bg-white border border-gray-200 hover:border-black hover:shadow-lg'}`}
      >
        {/* 面包屑文本 */}
        <div className="flex items-center gap-2 min-w-0">
          {/* 当前小节显示 */}
          {isLoading ? (
            <div className="flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
              <span className="text-sm text-gray-500">加载中...</span>
            </div>
          ) : currentSub ? (
            <div className="flex items-center gap-2 text-sm min-w-0">
              <span className="text-gray-500 truncate">当前学习:</span>
              <span className="font-medium text-black truncate max-w-[200px]" title={currentSub.subsection_title}>
                {currentSub.subsection_number} {currentSub.subsection_title}
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-500">选择小节</span>
            </div>
          )}
        </div>

        {/* 下拉箭头 */}
        {!disabled && (
          <motion.div
            animate={{ rotate: isOpen ? 180 : 0 }}
            transition={{ duration: 0.2 }}
            className={`flex-shrink-0 ${
              isOpen ? 'text-black' : 'text-gray-400'
            }`}
          >
            <ChevronDown className="w-4 h-4" />
          </motion.div>
        )}
      </div>

      {/* 下拉菜单 */}
      <AnimatePresence>
        {isOpen && !disabled && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="absolute top-full left-0 right-0 mt-2 z-[9999]"
          >
            <div className="bg-white border border-gray-200 rounded-2xl shadow-xl overflow-hidden !opacity-100">
              {/* 头部：章节信息 */}
              <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
                <p className="text-xs text-gray-500 uppercase tracking-wide">章节：{chapterTitle}</p>
                <p className="text-sm font-medium text-black">{currentSub ? `${currentSub.subsection_number} ${currentSub.subsection_title}` : '选择一个小节开始学习'}</p>
              </div>

              {/* 小节列表 */}
              <div className="max-h-64 overflow-y-auto py-2">
                {subsections.length === 0 ? (
                  <div className="px-4 py-6 text-center">
                    <p className="text-sm text-gray-500">
                      {isLoading ? '加载中...' : '该章节暂无小节划分'}
                    </p>
                  </div>
                ) : (
                  subsections.map((subsection, index) => {
                    const isSelected = subsection.subsection_number === currentSubsection
                    const isCompleted = subsection.completion_percentage >= 100

                    return (
                      <motion.button
                        key={subsection.subsection_number}
                        onClick={() => handleSubsectionSelect(subsection)}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05, duration: 0.2 }}
                        className={`w-full px-4 py-3 text-left flex items-center gap-3 transition-colors duration-150 ${isSelected ? 'bg-black text-white' : 'hover:bg-gray-100'}`}
                      >
                        {/* 状态图标 */}
                        <div className={`flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-xs ${isSelected ? 'bg-white text-black' : isCompleted ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-500'}`}>
                          {isCompleted ? '✓' : subsection.subsection_number.split('.').pop()?.substring(0, 2) || index + 1}
                        </div>

                        {/* 小节信息 */}
                        <div className="flex-1 min-w-0">
                          <div className={`text-sm font-medium truncate ${isSelected ? 'text-white' : 'text-black'}`}>
                            {subsection.subsection_number}
                          </div>
                          <div className={`text-xs truncate ${isSelected ? 'text-white/80' : 'text-gray-500'}`}>
                            {subsection.subsection_title}
                          </div>
                        </div>

                        {/* 完成度指示器 */}
                        {!isSelected && subsection.completion_percentage > 0 && (
                          <div className="flex-shrink-0 w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-black rounded-full transition-all duration-300"
                              style={{ width: `${subsection.completion_percentage}%` }}
                            />
                          </div>
                        )}
                      </motion.button>
                    )
                  })
                )}
              </div>

              {/* 底部提示 */}
              {subsections.length > 0 && (
                <div className="px-4 py-2 bg-gray-50 border-t border-gray-200">
                  <p className="text-xs text-gray-500">
                    💡 选择小节后，AI将根据该小节内容为你讲解
                  </p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
