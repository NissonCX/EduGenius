'use client'

import { motion } from 'framer-motion'
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
  MessageSquare
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

interface Chapter {
  id: string
  title: string
  status: 'completed' | 'in-progress' | 'locked'
  progress: number
}

interface SidebarProps {
  className?: string
}

const mockChapters: Chapter[] = [
  { id: '1', title: '第一章：线性代数基础', status: 'completed', progress: 100 },
  { id: '2', title: '第二章：向量空间', status: 'in-progress', progress: 65 },
  { id: '3', title: '第三章：矩阵运算', status: 'in-progress', progress: 30 },
  { id: '4', title: '第四章：特征值与特征向量', status: 'locked', progress: 0 },
  { id: '5', title: '第五章：线性变换', status: 'locked', progress: 0 },
]

export function Sidebar({ className }: SidebarProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const pathname = usePathname()
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [username, setUsername] = useState('')
  const [userLevel, setUserLevel] = useState('1')
  const overallProgress = Math.round(
    mockChapters.reduce((acc, ch) => acc + ch.progress, 0) / mockChapters.length
  )

  // 检查用户登录状态
  useEffect(() => {
    const token = localStorage.getItem('token')
    const storedUsername = localStorage.getItem('username')
    const storedLevel = localStorage.getItem('cognitive_level')

    setIsLoggedIn(!!token)
    setUsername(storedUsername || '')
    setUserLevel(storedLevel || '1')
  }, [])

  const navItems = [
    { href: '/', icon: Home, label: '首页' },
    { href: '/study', icon: MessageSquare, label: '学习对话' },
    { href: '/dashboard', icon: BarChart3, label: '仪表盘' }
  ]

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user_id')
    localStorage.removeItem('user_email')
    localStorage.removeItem('username')
    localStorage.removeItem('cognitive_level')
    window.location.href = '/'
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
    // Handle file upload logic here
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
          <div className="flex items-center justify-between mb-2">
            <div>
              <h1 className="text-xl font-semibold text-balance">EduGenius</h1>
              <p className="text-sm text-gray-500 mt-1">AI 自适应学习平台</p>
            </div>
          </div>

          {/* 用户状态 */}
          <div className="mt-4">
            {isLoggedIn ? (
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-black text-white flex items-center justify-center text-xs font-medium">
                    {username?.[0]?.toUpperCase() || 'U'}
                  </div>
                  <div>
                    <p className="text-sm font-medium">{username || '用户'}</p>
                    <p className="text-xs text-gray-500">L{userLevel}</p>
                  </div>
                </div>
                <button
                  onClick={handleLogout}
                  className="text-xs text-gray-600 hover:text-black transition-colors"
                >
                  退出
                </button>
              </div>
            ) : (
              <div className="flex gap-2">
                <Link
                  href="/login"
                  className="flex-1 px-3 py-2 bg-black text-white text-center text-sm rounded-lg hover:bg-gray-800 transition-colors"
                >
                  登录
                </Link>
                <Link
                  href="/register"
                  className="flex-1 px-3 py-2 border border-gray-200 text-center text-sm rounded-lg hover:bg-gray-50 transition-colors"
                >
                  注册
                </Link>
              </div>
            )}
          </div>
        </motion.div>
      </div>

      {/* Navigation */}
      <div className="px-4 py-2">
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href
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
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </Link>
            )
          })}
        </nav>
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
