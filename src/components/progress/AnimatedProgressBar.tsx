'use client'

/**
 * AnimatedProgressBar - 带流光效果的进度条
 * 答对题目时触发平滑的"增长流光"效果
 */

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'

interface AnimatedProgressBarProps {
  value: number // 0-100
  max?: number
  showPercentage?: boolean
  height?: string
  className?: string
  triggerAnimation?: boolean // 外部触发动画（如答对题目）
  onAnimationComplete?: () => void
}

export function AnimatedProgressBar({
  value,
  max = 100,
  showPercentage = true,
  height = '8px',
  className = '',
  triggerAnimation = false,
  onAnimationComplete
}: AnimatedProgressBarProps) {
  const [currentValue, setCurrentValue] = useState(value)
  const [isAnimating, setIsAnimating] = useState(false)

  // 更新进度值
  useEffect(() => {
    setCurrentValue(value)
  }, [value])

  // 触发流光动画
  useEffect(() => {
    if (triggerAnimation) {
      setIsAnimating(true)
      setTimeout(() => setIsAnimating(false), 1500) // 动画持续 1.5 秒
      onAnimationComplete?.()
    }
  }, [triggerAnimation, onAnimationComplete])

  const percentage = Math.min(100, Math.max(0, (currentValue / max) * 100))

  return (
    <div className={`relative w-full ${className}`}>
      {/* 进度条容器 */}
      <div
        className="w-full bg-gray-100 rounded-full overflow-hidden"
        style={{ height }}
      >
        {/* 背景进度条 */}
        <motion.div
          className="h-full bg-black rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
        />

        {/* 流光效果 */}
        {isAnimating && (
          <motion.div
            className="absolute top-0 left-0 h-full rounded-full"
            initial={{ x: '-100%' }}
            animate={{ x: '100%' }}
            transition={{
              duration: 1.5,
              ease: 'linear',
              repeat: Infinity
            }}
            style={{
              background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)',
              width: '100%'
            }}
          />
        )}

      </div>

      {/* 百分比显示 */}
      {showPercentage && (
        <div className="flex justify-between items-center mt-2">
          <span className="text-xs text-gray-500">学习进度</span>
          <motion.span
            key={percentage}
            initial={{ scale: 1.2, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="text-sm font-semibold text-black"
          >
            {Math.round(percentage)}%
          </motion.span>
        </div>
      )}

    </div>
  )
}
