'use client'

/**
 * StrictnessMenu - 导师风格浮动菜单
 * 输入框右侧的小型浮动菜单，用于调节导师教学风格
 */

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Settings } from 'lucide-react'

interface StrictnessMenuProps {
  currentLevel: number | null
  onChange: (level: number) => void
}

export function StrictnessMenu({ currentLevel, onChange }: StrictnessMenuProps) {
  const [isOpen, setIsOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  // 点击外部关闭菜单
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const levels = [
    { value: 1, label: '温柔', description: '耐心细致', color: 'bg-emerald-500' },
    { value: 2, label: '耐心', description: '循序渐进', color: 'bg-blue-500' },
    { value: 3, label: '标准', description: '平衡严谨', color: 'bg-indigo-500' },
    { value: 4, label: '严格', description: '注重细节', color: 'bg-orange-500' },
    { value: 5, label: '严厉', description: '挑战思维', color: 'bg-red-500' }
  ]

  const currentLevelData = currentLevel !== null ? levels.find(l => l.value === currentLevel) : null

  return (
    <div ref={menuRef} className="relative">
      {/* 触发按钮 */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(!isOpen)}
        className={`w-10 h-10 rounded-xl border flex items-center justify-center transition-all duration-200 ${
          isOpen
            ? 'bg-black border-black text-white shadow-lg'
            : 'bg-white border-gray-200 hover:border-gray-300 text-gray-600'
        }`}
        title="调节导师风格"
      >
        <Settings className="w-4 h-4" />
      </motion.button>

      {/* 浮动菜单 */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 8, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.96 }}
            transition={{ duration: 0.15, ease: 'easeOut' }}
            className="absolute right-0 bottom-14 w-48 bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden z-50"
          >
            <div className="p-2">
              <p className="text-xs font-medium text-gray-500 px-3 py-2 mb-1">导师风格</p>

              <div className="space-y-1">
                {levels.map((level, index) => {
                  const isSelected = currentLevel === level.value

                  return (
                    <motion.button
                      key={level.value}
                      whileHover={{ x: 2 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => {
                        onChange(level.value)
                        setIsOpen(false)
                      }}
                      className={`w-full px-3 py-2.5 rounded-xl text-left transition-all duration-150 ${
                        isSelected
                          ? 'bg-black text-white shadow-md'
                          : 'hover:bg-gray-50 text-gray-700'
                      }`}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.03 }}
                    >
                      <div className="flex items-center gap-3">
                        {/* 颜色指示器 */}
                        <div className={`w-2 h-2 rounded-full ${level.color} ${
                          isSelected ? 'bg-white' : ''
                        }`} />

                        {/* 风格名称 */}
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold">L{level.value}</span>
                            <span className="text-sm font-medium">{level.label}</span>
                          </div>
                          <p className={`text-xs mt-0.5 ${isSelected ? 'text-gray-300' : 'text-gray-500'}`}>
                            {level.description}
                          </p>
                        </div>

                        {/* 选中标记 */}
                        {isSelected && (
                          <motion.div
                            initial={{ scale: 0, rotate: -90 }}
                            animate={{ scale: 1, rotate: 0 }}
                            transition={{ delay: index * 0.03 + 0.1, type: 'spring', stiffness: 200 }}
                          >
                            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                            </svg>
                          </motion.div>
                        )}
                      </div>
                    </motion.button>
                  )
                })}
              </div>

              {/* 提示文字 */}
              <div className="px-3 py-2 mt-1">
                <p className="text-xs text-gray-400 text-center">
                  临时调整，不影响偏好设置
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
