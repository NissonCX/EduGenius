import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import '@/styles/globals.css';
import 'katex/dist/katex.min.css';
import { Sidebar } from '@/components/layout/Sidebar';
import { MobileNav } from '@/components/layout/MobileNav';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { ToastProvider } from '@/components/Toast';
import { AuthProvider } from '@/contexts/AuthContext';
import PWAInstaller from '@/components/PWAInstaller';
import { motion, AnimatePresence } from 'framer-motion';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
})

export const metadata: Metadata = {
  title: 'EduGenius - AI 自适应教育平台',
  description: '基于 LangGraph 多智能体架构的高端 AI 自适应学习平台',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'EduGenius',
  },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: '#000000',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN" className={inter.variable}>
      <head>
        <link rel="manifest" href="/manifest.json" />
        <link rel="icon" href="/icon-192.png" />
        <link rel="apple-touch-icon" href="/icon-192.png" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="EduGenius" />
      </head>
      <body className="antialiased">
        <AuthProvider>
          <ToastProvider>
            <ErrorBoundary>
              {/* PWA 安装提示组件 */}
              <PWAInstaller />

              {/* 桌面端侧边栏 - 固定定位 */}
              <div className="hidden lg:block">
                <Sidebar />
              </div>

              {/* 主内容区域 - 桌面端添加左边距，移动端添加底部内边距 */}
              <main className="min-h-screen lg:pl-80 pb-16 lg:pb-0">
                <AnimatePresence mode="wait">
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{
                      duration: 0.2,
                      ease: [0.4, 0, 0.2, 1]
                    }}
                  >
                    {children}
                  </motion.div>
                </AnimatePresence>
              </main>

              {/* 移动端底部导航 - 仅在移动端显示 */}
              <MobileNav />
            </ErrorBoundary>
          </ToastProvider>
        </AuthProvider>
        <script>{`
          // 注册 Service Worker
          if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
              navigator.serviceWorker.register('/sw.js')
                .then((registration) => {
                  console.log('SW registered: ', registration);
                })
                .catch((registrationError) => {
                  console.log('SW registration failed: ', registrationError);
                });
            });
          }
        `}</script>
      </body>
    </html>
  )
}
