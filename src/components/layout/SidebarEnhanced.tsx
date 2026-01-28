'use client'

/**
 * EnhancedSidebar - 增强侧边栏
 * 包含错题本图标（带微颤动效）和严厉程度调节滑块
 */

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  FileText,
  Upload,
  ChevronRight,
  BookOpen,
  CheckCircle2,
  Circle,
  Lock,
  BarChart3,
  Home,
  AlertCircle,
  Sun,
  Scale,
  MessageSquare
} from 'lucide-react'
import { cn } from '@/lib/utils'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

interface Chapter {
  id: string
  title: string
  status: 'completed' | 'in-progress' | 'locked'
  progress: number
}

interface SidebarEnhancedProps {
  className?: string
  onErrorCountChange?: (count: number) => void
  onErrorTrigger?: () => void // 外部触发错题动画
  onStrictnessChange?: (level: number) => void // 严厉程度回调
}

const mockChapters: Chapter[] = [
  { id: '1', title: '第一章：线性代数基础', status: 'completed', progress: 100 },
  { id: '2', title: '第二章：向量空间', status: 'in-progress', progress: 65 },
  { id: '3', title: '第三章：矩阵运算', status: 'in-progress', progress: 30 },
  { id: '4', title: '第四章：特征值与特征向量', status: 'locked', progress: 0 },
  { id: '5', title: '第五章：线性变换', status: 'locked', progress: 0 },
]

export function SidebarEnhanced({
  className,
  onErrorTrigger,
  onStrictnessChange
}: SidebarEnhancedProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [errorCount, setErrorCount] = useState(0)
  const [shakeError, setShakeError] = useState(false)
  const [strictness, setStrictness] = useState(3) // 1-5 严厉程度
  const pathname = usePathname()

  const overallProgress = Math.round(
    mockChapters.reduce((acc, ch) => acc + ch.progress, 0) / mockChapters.length
  )

  const navItems = [
    { href: '/', icon: Home, label: '首页' },
    { href: '/study', icon: MessageSquare, label: '学习对话' },
    { href: '/dashboard', icon: BarChart3, label: '仪表盘' },
    {
      href: '/mistakes',
      icon: AlertCircle,
      label: '错题本',
      badge: errorCount > 0 ? errorCount : undefined,
      shake: shakeError
    }
  ]

  // 监听外部触发错题动画
  useEffect(() => {
    if (onErrorTrigger) {
      const handleTrigger = () => {
        setErrorCount(prev => prev + 1)
        setShakeError(true)
        setTimeout(() => setShakeError(false), 500) // 震动 500ms
      }
      onErrorTrigger()
    }
  }, [onErrorTrigger])

  // 严厉程度标签
  const getStrictnessLabel = (level: number) => {
    const labels = {
      1: '温柔引导',
      2: '耐心细致',
      3: '标准教学',
      4: '严格要求',
      5: '严格督促'
    }
    return labels[level as keyof typeof labels] || labels[3]
  }

  const getStrictnessColor = (level: number) => {
    if (level <= 2) return 'text-emerald-600'
    if (level === 3) return 'text-blue-600'
    return 'text-orange-600'
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = () => {
    setIsDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    const files = Array.from(e.dataTransfer.files)
    console.log('Files dropped:', files)
  }

  const ChapterIcon = ({ status }: { status: Chapter['status'] }) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-emerald-500" />
      case 'in-progress':
        return <Circle className="w-4 h-4 text-blue-500 fill-blue-500/20" />
      case 'locked':
        return <Lock className="w-4 h-4 text-muted-foreground" />
    }
  }

  return (
    <aside className={cn(
      "w-80 h-screen bg-white border-r border-gray-200 flex flex-col",
      className
    )}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <h1 className="text-xl font-semibold text-balance">EduGenius</h1>
          <p className="text-sm text-gray-500 mt-1">AI 自适应学习平台</p>
        </motion.div>
      </div>

      {/* Navigation */}
      <div className="px-4 py-2">
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href
            const isShaking = item.shake

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-xl transition-all duration-200",
                  "text-sm font-medium",
                  isActive
                    ? "bg-black text-white"
                    : "text-gray-700 hover:bg-gray-100"
                )}
              >
                <motion.div
                  animate={isShaking ? {
                    x: [0, -3, 3, -3, 3, 0],
                    rotate: [0, -5, 5, -5, 5, 0]
                  } : {}}
                  transition={{ duration: 0.4 }}
                >
                  <Icon className="w-4 h-4" />
                </motion.div>
                <span className="flex-1">{item.label}</span>
                {item.badge && (
                  <motion.span
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="px-2 py-0.5 bg-red-500 text-white text-xs rounded-full"
                  >
                    {item.badge}
                  </motion.span>
                )}
              </Link>
            )
          })}
        </nav>
      </div>

      {/* 严厉程度调节 */}
      <div className="px-4 py-3">
        <motion.div
          className="p-4 bg-gray-50 rounded-xl border border-gray-200"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="flex items-center gap-2 mb-3">
            <Scale className="w-4 h-4 text-gray-600" />
            <span className="text-sm font-medium text-gray-700">导师风格</span>
          </div>

          {/* 严厉程度标签 */}
          <motion.div
            key={strictness}
            initial={{ scale: 1.1 }}
            animate={{ scale: 1 }}
            className="mb-3"
          >
            <span className={cn("text-sm font-semibold", getStrictnessColor(strictness))}>
              {getStrictnessLabel(strictness)}
            </span>
            <span className="text-xs text-gray-500 ml-2">L{strictness}</span>
          </motion.div>

          {/* 滑块 */}
          <div className="flex items-center gap-3">
            <Sun className="w-4 h-4 text-gray-400" />
            <input
              type="range"
              min="1"
              max="5"
              value={strictness}
              onChange={(e) => {
                const newLevel = parseInt(e.target.value)
                setStrictness(newLevel)
                onStrictnessChange?.(newLevel)
              }}
              className="flex-1 h-1.5 bg-gray-200 rounded-full appearance-none cursor-pointer
                [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4
                [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:bg-black
                [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:cursor-pointer
                [&::-webkit-slider-thumb]:transition-transform [&::-webkit-slider-thumb]:hover:scale-110"
            />
            <span className="text-xs text-gray-600 w-4">L5</span>
          </div>

          <p className="text-xs text-gray-500 mt-2">
            {strictness <= 2 ? '多鼓励，少压力' : strictness === 3 ? '平衡教学' : '高标准，严要求'}
          </p>
        </motion.div>
      </div>

      {/* File Upload Area */}
      <div className="p-4">
        <motion.div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={cn(
            "card-base p-6 cursor-pointer transition-all duration-200",
            isDragOver && "border-blue-500 shadow-md"
          )}
          whileHover={{ scale: 1.01, boxShadow: "0 4px 12px rgba(0,0,0,0.08)" }}
          whileTap={{ scale: 0.99 }}
        >
          <div className="flex flex-col items-center text-center space-y-3">
            <motion.div
              className="w-12 h-12 rounded-full bg-gray-50 flex items-center justify-center"
              whileHover={{ rotate: 180 }}
              transition={{ duration: 0.3 }}
            >
              <Upload className="w-5 h-5 text-black" />
            </motion.div>
            <div>
              <p className="text-sm font-medium">上传教材</p>
              <p className="text-xs text-gray-500 mt-1">
                拖拽 PDF 或 TXT 文件至此
              </p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Progress Ring */}
      <div className="p-4">
        <motion.div
          className="card-base p-4"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.2 }}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">学习进度</p>
              <p className="text-2xl font-semibold mt-1">{overallProgress}%</p>
            </div>
            <svg className="w-16 h-16 -rotate-90" viewBox="0 0 36 36">
              <path
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="currentColor"
                strokeWidth="0.5"
                className="text-gray-200"
              />
              <motion.path
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeDasharray={`${overallProgress}, 100`}
                className="text-black"
                initial={{ strokeDasharray: "0, 100" }}
                animate={{ strokeDasharray: `${overallProgress}, 100` }}
                transition={{ duration: 0.5, ease: "easeOut" }}
              />
            </svg>
          </div>
        </motion.div>
      </div>

      {/* Chapter Navigation */}
      <div className="flex-1 overflow-y-auto px-4 pb-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-medium text-gray-500">章节目录</h2>
          <span className="text-xs text-gray-500">
            {mockChapters.filter(c => c.status !== 'locked').length}/{mockChapters.length}
          </span>
        </div>

        <nav className="space-y-1">
          {mockChapters.map((chapter, index) => (
            <motion.div
              key={chapter.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.2, delay: index * 0.05 }}
            >
              <button
                className={cn(
                  "w-full flex items-center justify-between p-3 rounded-xl transition-all duration-200",
                  "border border-transparent hover:border-gray-200 hover:shadow-sm",
                  chapter.status === 'in-progress' && "border-gray-200 bg-gray-50/50",
                  chapter.status === 'locked' && "opacity-50 cursor-not-allowed"
                )}
                disabled={chapter.status === 'locked'}
              >
                <div className="flex items-center space-x-3">
                  <ChapterIcon status={chapter.status} />
                  <span className="text-sm text-left">{chapter.title}</span>
                </div>
                {chapter.status !== 'locked' && (
                  <ChevronRight className="w-4 h-4 text-gray-400" />
                )}
              </button>
            </motion.div>
          ))}
        </nav>
      </div>
    </aside>
  )
}
