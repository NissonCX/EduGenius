'use client'

/**
 * MobileNav - 移动端底部导航栏
 * 提供快速访问主要功能的导航
 */

import { useState, useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { Home, BookOpen, FileText, BarChart3, Menu, X } from 'lucide-react'

interface NavItem {
  id: string
  label: string
  icon: React.ComponentType<{ className?: string }>
  path: string
}

const NAV_ITEMS: NavItem[] = [
  { id: 'dashboard', label: '首页', icon: Home, path: '/dashboard' },
  { id: 'study', label: '学习', icon: BookOpen, path: '/study' },
  { id: 'documents', label: '文档', icon: FileText, path: '/documents' },
  { id: 'mistakes', label: '错题', icon: BarChart3, path: '/mistakes' },
]

export function MobileNav() {
  const router = useRouter()
  const pathname = usePathname()
  const [isMobile, setIsMobile] = useState(false)
  const [showMenu, setShowMenu] = useState(false)

  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768
      setIsMobile(mobile)
    }

    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // 如果不是移动端，不显示底部导航
  if (!isMobile) return null

  const activePath = pathname

  return (
    <>
      {/* 底部导航栏 */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50 safe-area-bottom">
        <div className="flex items-center justify-around h-16 px-2">
          {NAV_ITEMS.map((item) => {
            const isActive = activePath === item.path || activePath.startsWith(item.path + '/')
            const Icon = item.icon

            return (
              <motion.button
                key={item.id}
                onClick={() => router.push(item.path)}
                className="flex flex-col items-center justify-center flex-1 py-2 relative"
                whileTap={{ scale: 0.95 }}
              >
                {/* 活跃指示器 */}
                {isActive && (
                  <motion.div
                    layoutId="activeTab"
                    className="absolute -top-0.5 left-1/2 transform -translate-x-1/2 w-8 h-0.5 bg-black"
                    transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                  />
                )}

                {/* 图标 */}
                <div className={`mb-1 ${isActive ? 'text-black' : 'text-gray-400'}`}>
                  <Icon className="w-5 h-5" />
                </div>

                {/* 标签 */}
                <span className={`text-[10px] font-medium ${isActive ? 'text-black' : 'text-gray-400'}`}>
                  {item.label}
                </span>
              </motion.button>
            )
          })}
        </div>
      </nav>

      {/* 添加底部安全区域（用于 iPhone X 及以上设备） */}
      <style jsx global>{`
        .safe-area-bottom {
          padding-bottom: env(safe-area-inset-bottom, 0px);
        }
      `}</style>
    </>
  )
}
