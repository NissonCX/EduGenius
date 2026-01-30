'use client'

/**
 * 沉浸式文档上传页面
 *
 * 特性：
 * - 玻璃拟态设计
 * - 动态渐变背景
 * - SmartUpload 核心组件
 * - 平滑进度插值
 * - 高级通知系统
 */

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { X, BookOpen, CheckCircle, AlertCircle } from 'lucide-react'
import { SmartUpload } from '@/components/upload/SmartUpload'
import { useToast } from '@/hooks/use-toast-simple'
import { useAuth } from '@/contexts/AuthContext'

// 平滑进度插值 Hook
function useSmoothProgress(targetProgress: number, duration: number = 500) {
  const [smoothProgress, setSmoothProgress] = useState(0)

  useEffect(() => {
    if (targetProgress === 0) {
      setSmoothProgress(0)
      return
    }

    const startValue = smoothProgress
    const difference = targetProgress - startValue
    const startTime = Date.now()

    const animate = () => {
      const now = Date.now()
      const elapsed = now - startTime
      const progress = Math.min(elapsed / duration, 1)

      // 使用 easeOutQuart 缓动函数
      const easeOutQuart = (t: number) => 1 - Math.pow(1 - t, 4)
      const currentValue = startValue + difference * easeOutQuart(progress)

      setSmoothProgress(currentValue)

      if (progress < 1) {
        requestAnimationFrame(animate)
      } else {
        setSmoothProgress(targetProgress)
      }
    }

    requestAnimationFrame(animate)
  }, [targetProgress, duration])

  return smoothProgress
}

export default function UploadPage() {
  const router = useRouter()
  const { isAuthenticated } = useAuth()
  const { toast, toasts, dismiss } = useToast()

  // 处理上传完成
  const handleUploadComplete = (documentId: number) => {
    // 延迟跳转，让用户看到完成状态
    setTimeout(() => {
      // 显示成功通知
      toast({
        title: "✅ 文档上传成功",
        description: "正在前往文档列表...",
        duration: 2000,
      })

      // 跳转到文档列表（这样用户能立即看到新文档）
      router.push('/documents')
    }, 1500)
  }

  // 处理上传错误
  const handleError = (error: string) => {
    toast({
      title: "❌ 上传失败",
      description: error,
      variant: "destructive",
      duration: 5000,
    })
  }

  // 未登录处理
  if (isAuthenticated === false) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-semibold text-gray-900 mb-4">请先登录</h1>
          <button
            onClick={() => router.push('/login')}
            className="px-6 py-3 bg-black text-white rounded-xl hover:bg-gray-800 transition-colors"
          >
            前往登录
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* 动态渐变背景 */}
      <div className="fixed inset-0 -z-10">
        {/* 基础渐变 */}
        <div className="absolute inset-0 bg-gradient-to-br from-gray-50 via-blue-50 to-purple-50" />

        {/* 动态光晕效果 */}
        <motion.div
          className="absolute top-0 left-1/4 w-96 h-96 bg-blue-400/20 rounded-full blur-3xl"
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.5, 0.3],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        <motion.div
          className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-400/20 rounded-full blur-3xl"
          animate={{
            scale: [1.2, 1, 1.2],
            opacity: [0.5, 0.3, 0.5],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />

        {/* 网格纹理 */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `
              linear-gradient(rgba(0,0,0,0.1) 1px, transparent 1px),
              linear-gradient(90deg, rgba(0,0,0,0.1) 1px, transparent 1px)
            `,
            backgroundSize: '50px 50px'
          }}
        />
      </div>

      {/* 主内容区 */}
      <div className="relative z-10 min-h-screen flex flex-col">
        {/* 顶部导航 */}
        <nav className="flex items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-black to-gray-800 rounded-xl flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-xl font-semibold text-black">EduGenius</h1>
          </div>

          <button
            onClick={() => router.push('/documents')}
            className="p-2 hover:bg-white/50 rounded-lg transition-colors"
          >
            <X className="w-6 h-6 text-gray-600" />
          </button>
        </nav>

        {/* 中央上传区域 */}
        <div className="flex-1 flex items-center justify-center px-6 py-12">
          <div className="w-full max-w-3xl">
            {/* SmartUpload 组件 */}
            <SmartUpload
              onUploadComplete={handleUploadComplete}
              onError={handleError}
            />

            {/* 底部提示 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.8 }}
              className="mt-8 text-center"
            >
              <p className="text-sm text-gray-600 mb-2">
                支持 PDF 格式，最大 50MB
              </p>
              <div className="flex items-center justify-center gap-6 text-xs text-gray-500">
                <span>✨ 智能识别文本层</span>
                <span>⚡ 快速处理</span>
                <span>🔬 OCR 扫描件支持</span>
              </div>
            </motion.div>
          </div>
        </div>

        {/* Toast 通知容器 */}
        <AnimatePresence>
          {toasts.map((t) => (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, y: 50, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 20, scale: 0.95 }}
              transition={{ duration: 0.3 }}
              className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50"
            >
              <div className={`
                px-6 py-4 rounded-2xl shadow-2xl border
                ${t.variant === 'destructive'
                  ? 'bg-red-500 text-white border-red-600'
                  : 'bg-white text-gray-900 border-gray-200'}
              `}>
                <div className="flex items-center gap-3">
                  {t.variant === 'destructive' ? (
                    <AlertCircle className="w-5 h-5 flex-shrink-0" />
                  ) : (
                    <CheckCircle className="w-5 h-5 flex-shrink-0" />
                  )}
                  <div>
                    <p className="font-medium text-sm">{t.title}</p>
                    {t.description && (
                      <p className="text-sm opacity-90 mt-1">{t.description}</p>
                    )}
                  </div>
                  <button
                    onClick={() => dismiss(t.id)}
                    className="ml-2 opacity-60 hover:opacity-100"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  )
}
