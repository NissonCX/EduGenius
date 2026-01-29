'use client'

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
  MessageSquare,
  AlertCircle
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'

interface Chapter {
  id: string
  title: string
  status: 'completed' | 'in-progress' | 'locked'
  progress: number
  is_locked?: boolean
  lock_reason?: string
}

interface SidebarProps {
  className?: string
}

export function Sidebar({ className }: SidebarProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const pathname = usePathname()
  const router = useRouter()
  const [chapters, setChapters] = useState<Chapter[]>([])
  const [isLoadingChapters, setIsLoadingChapters] = useState(true)
  const [lockToast, setLockToast] = useState<{ show: boolean; message: string }>({ show: false, message: '' })

  // 使用 useAuth hook
  const { user, isAuthenticated, logout } = useAuth()

  // 加载真实章节数据
  useEffect(() => {
    const loadChapters = async () => {
      if (!isAuthenticated || !user.id) {
        setChapters([])
        setIsLoadingChapters(false)
        return
      }

      try {
        const response = await fetch(
          `http://localhost:8000/api/users/${user.id}/progress`,
          {
            headers: {
              'Content-Type': 'application/json',
              ...(user.token && { 'Authorization': `Bearer ${user.token}` })
            }
          }
        )

        if (response.ok) {
          const progressData = await response.json()

          // 转换为 Chapter 格式
          const chapterList: Chapter[] = progressData.map((p: any) => ({
            id: p.chapter_number.toString(),
            title: p.chapter_title || `第${p.chapter_number}章`,
            status: p.status as 'completed' | 'in-progress' | 'locked',
            progress: Math.round(p.completion_percentage)
          }))

          setChapters(chapterList)
        } else {
          // 如果 API 失败，使用空数组
          setChapters([])
        }
      } catch (error) {
        console.error('加载章节失败:', error)
        setChapters([])
      } finally {
        setIsLoadingChapters(false)
      }
    }

    loadChapters()
  }, [user.id, isAuthenticated, user.token])

  // 计算总体进度
  const overallProgress = chapters.length > 0
    ? Math.round(chapters.reduce((acc, ch) => acc + ch.progress, 0) / chapters.length)
    : 0

  const navItems = [
    { href: '/', icon: Home, label: '首页' },
    { href: '/documents', icon: FileText, label: '文档管理' },
    { href: '/study', icon: MessageSquare, label: '学习对话' },
    { href: '/dashboard', icon: BarChart3, label: '仪表盘' }
  ]

  const handleLogout = () => {
    logout()
    window.location.href = '/'
  }

  const handleChapterClick = (chapter: Chapter) => {
    if (chapter.is_locked || chapter.status === 'locked') {
      // 显示锁定提示
      setLockToast({
        show: true,
        message: chapter.lock_reason || '此章节尚未解锁，请先完成前置章节。'
      })

      // 3秒后自动隐藏提示
      setTimeout(() => {
        setLockToast({ show: false, message: '' })
      }, 3000)
      return
    }

    // 跳转到学习页面
    router.push(`/study?chapter=${chapter.id}`)
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
            {isAuthenticated && user ? (
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-black text-white flex items-center justify-center text-xs font-medium">
                    {user.username?.[0]?.toUpperCase() || 'U'}
                  </div>
                  <div>
                    <p className="text-sm font-medium">{user.username || '用户'}</p>
                  </div>
                </div>
                <button
                  onClick={handleLogout}
                  className="text-xs text-gray-600 hover:text-black transition-colors px-3 py-1.5 rounded-lg hover:bg-gray-200"
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
            {chapters.filter(c => !c.is_locked && c.status !== 'locked').length}/{chapters.length || 0}
          </span>
        </div>

        {/* 锁定提示 Toast */}
        <AnimatePresence>
          {lockToast.show && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mb-3 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2"
            >
              <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-amber-900">章节未解锁</p>
                <p className="text-xs text-amber-700 mt-1">{lockToast.message}</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <nav className="space-y-1">
          {isLoadingChapters ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-black"></div>
            </div>
          ) : chapters.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-sm text-gray-500">
                {isAuthenticated ? '暂无学习记录' : '登录后查看学习进度'}
              </p>
            </div>
          ) : (
            chapters.map((chapter, index) => (
              <motion.div
                key={chapter.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.2, delay: index * 0.05 }}
              >
                <button
                  onClick={() => handleChapterClick(chapter)}
                  className={cn(
                    "w-full flex items-center justify-between p-3 rounded-xl transition-all duration-200",
                    "border border-transparent hover:border-gray-200 hover:shadow-sm",
                    chapter.status === 'in-progress' && "border-gray-200 bg-gray-50/50",
                    (chapter.is_locked || chapter.status === 'locked') && "opacity-60 hover:border-gray-100"
                  )}
                >
                  <div className="flex items-center space-x-3">
                    <ChapterIcon status={chapter.status} />
                    <div className="text-left">
                      <span className="text-sm">{chapter.title}</span>
                      {(chapter.is_locked || chapter.status === 'locked') && chapter.lock_reason && (
                        <p className="text-xs text-gray-500 mt-0.5 line-clamp-1">
                          {chapter.lock_reason}
                        </p>
                      )}
                    </div>
                  </div>
                  {!(chapter.is_locked || chapter.status === 'locked') && (
                    <ChevronRight className="w-4 h-4 text-gray-400" />
                  )}
                </button>
              </motion.div>
            ))
          )}
        </nav>
      </div>
    </aside>
  )
}
