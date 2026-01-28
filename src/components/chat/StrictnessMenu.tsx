'use client'

/**
 * StrictnessMenu - 严厉程度浮动菜单
 * 输入框右侧的小型浮动菜单，用于调节导师严厉程度
 */

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Scale } from 'lucide-react'

interface StrictnessMenuProps {
  currentLevel: number
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
    { value: 1, label: '温柔', color: 'text-emerald-600' },
    { value: 2, label: '耐心', color: 'text-blue-600' },
    { value: 3, label: '标准', color: 'text-purple-600' },
    { value: 4, label: '严格', color: 'text-orange-600' },
    { value: 5, label: '严厉', color: 'text-red-600' }
  ]

  const currentLevelData = levels.find(l => l.value === currentLevel) || levels[2]

  return (
    <div ref={menuRef} className="relative">
      {/* 触发按钮 */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(!isOpen)}
        className={`w-10 h-10 rounded-lg border border-gray-200 flex items-center justify-center transition-colors ${
          isOpen ? 'bg-gray-100' : 'bg-white hover:bg-gray-50'
        }`}
        title="调节导师严厉程度"
      >
        <Scale className="w-4 h-4 text-gray-600" />
      </motion.button>

      {/* 浮动菜单 */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 bottom-14 w-40 bg-white border border-gray-200 rounded-xl shadow-lg overflow-hidden z-50"
          >
            <div className="p-2">
              <p className="text-xs text-gray-500 px-2 py-1 mb-1">导师风格</p>
              {levels.map((level) => (
                <button
                  key={level.value}
                  onClick={() => {
                    onChange(level.value)
                    setIsOpen(false)
                  }}
                  className={`w-full px-3 py-2 rounded-lg text-left text-sm transition-colors flex items-center gap-2 ${
                    currentLevel === level.value
                      ? 'bg-black text-white'
                      : 'hover:bg-gray-100 text-gray-700'
                  }`}
                >
                  <span className={`font-semibold ${currentLevel === level.value ? 'text-white' : level.color}`}>
                    L{level.value}
                  </span>
                  <span>{level.label}</span>
                  {currentLevel === level.value && (
                    <motion.span
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="ml-auto w-1.5 h-1.5 rounded-full bg-white"
                    />
                  )}
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
