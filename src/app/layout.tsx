import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import '@/styles/globals.css'
import { Sidebar } from '@/components/layout/Sidebar'
import { MobileNav } from '@/components/layout/MobileNav'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { ToastProvider } from '@/components/Toast'
import { AuthProvider } from '@/contexts/AuthContext'

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
})

export const metadata: Metadata = {
  title: 'EduGenius - AI 自适应教育平台',
  description: '基于 LangGraph 多智能体架构的高端 AI 自适应学习平台',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN" className={inter.variable}>
      <body className="antialiased">
        <AuthProvider>
          <ToastProvider>
            <ErrorBoundary>
              <div className="flex min-h-screen lg:h-screen lg:overflow-hidden">
                {/* 桌面端侧边栏 - 移动端隐藏 */}
                <div className="hidden lg:block">
                  <Sidebar />
                </div>

                {/* 主内容区域 - 移动端添加底部内边距以避开导航栏 */}
                <main className="flex-1 overflow-y-auto lg:overflow-y-auto pb-16 lg:pb-0">
                  {children}
                </main>
              </div>

              {/* 移动端底部导航 - 仅在移动端显示 */}
              <MobileNav />
            </ErrorBoundary>
          </ToastProvider>
        </AuthProvider>
      </body>
    </html>
  )
}
