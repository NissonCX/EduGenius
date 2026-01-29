'use client'

import {
  FileText,
  Upload,
  BookOpen,
  BarChart3,
  Home,
  MessageSquare
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { getApiUrl } from '@/lib/config'

interface SidebarProps {
  className?: string
}

export function Sidebar({ className }: SidebarProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const pathname = usePathname()
  const [overallProgress, setOverallProgress] = useState(0)

  // 使用 useAuth hook
  const { user, isAuthenticated, logout } = useAuth()

  // 加载用户总体进度
  useEffect(() => {
    const loadProgress = async () => {
      if (!isAuthenticated || !user.id) {
        setOverallProgress(0)
        return
      }

      try {
        const response = await fetch(
          getApiUrl(`/api/users/${user.id}/progress`),
          {
            headers: {
              'Content-Type': 'application/json',
              ...(user.token && { 'Authorization': `Bearer ${user.token}` })
            }
          }
        )

        if (response.ok) {
          const progressData = await response.json()
          // 计算总体进度
          if (progressData.length > 0) {
            const avgProgress = progressData.reduce((acc: number, p: any) =>
              acc + p.completion_percentage, 0) / progressData.length
            setOverallProgress(Math.round(avgProgress))
          }
        }
      } catch (error) {
        console.error('加载进度失败:', error)
      }
    }

    loadProgress()
  }, [user.id, isAuthenticated])

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
    const validFiles = files.filter(file => {
      const ext = file.name.split('.').pop()?.toLowerCase()
      return ext === 'pdf' || ext === 'txt'
    })
    
    if (validFiles.length > 0) {
      // 跳转到文档管理页面
      window.location.href = '/documents'
    }
  }

  return (
    <aside className={cn(
      "w-80 h-screen bg-white border-r border-gray-200 flex flex-col",
      className
    )}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div>
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
        </div>
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
        <Link href="/documents">
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={cn(
              "card-base p-6 cursor-pointer transition-all duration-200",
              isDragOver && "border-blue-500 shadow-md"
            )}
          >
            <div className="flex flex-col items-center text-center space-y-3">
              <div className="w-12 h-12 rounded-full bg-gray-50 flex items-center justify-center">
                <Upload className="w-5 h-5 text-black" />
              </div>
              <div>
                <p className="text-sm font-medium">上传教材</p>
                <p className="text-xs text-gray-500 mt-1">
                  点击进入文档管理
                </p>
              </div>
            </div>
          </div>
        </Link>
      </div>

      {/* Progress Ring */}
      <div className="p-4">
        <div className="card-base p-4">
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
              <path
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeDasharray={`${overallProgress}, 100`}
                className="text-black"
              />
            </svg>
          </div>
        </div>
      </div>

      {/* 学习提示 */}
      <div className="flex-1 px-4 pb-4">
        <div className="card-base p-4">
          <div className="text-center">
            <BookOpen className="w-8 h-8 text-gray-400 mx-auto mb-3" />
            <p className="text-sm font-medium text-gray-900 mb-2">开始学习</p>
            <p className="text-xs text-gray-500 leading-relaxed">
              {isAuthenticated 
                ? '前往「学习对话」选择教材和章节开始学习'
                : '登录后即可开始您的学习之旅'
              }
            </p>
            {isAuthenticated && (
              <Link
                href="/study"
                className="mt-4 inline-block px-4 py-2 bg-black text-white text-sm rounded-lg hover:bg-gray-800 transition-colors"
              >
                开始学习
              </Link>
            )}
          </div>
        </div>
      </div>
    </aside>
  )
}
