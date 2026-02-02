'use client'

/**
 * PWAInstaller - PWA 安装提示组件
 *
 * 检测 PWA 安装条件，并在适当时显示安装提示
 */
import { useEffect, useState } from 'react'
import { Download, X } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

export default function PWAInstaller() {
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null)
  const [showPrompt, setShowPrompt] = useState(false)

  useEffect(() => {
    const handler = (e: Event) => {
      e.preventDefault()
      setDeferredPrompt(e)
      setShowPrompt(true)
    }

    window.addEventListener('beforeinstallprompt', handler)

    return () => {
      window.removeEventListener('beforeinstallprompt', handler)
    }
  }, [])

  const handleInstall = async () => {
    if (!deferredPrompt) return

    deferredPrompt.prompt()
    const { outcome } = await deferredPrompt.userChoice

    if (outcome === 'accepted') {
      console.log('PWA installed')
    }

    setDeferredPrompt(null)
    setShowPrompt(false)
  }

  const handleDismiss = () => {
    setShowPrompt(false)
    // 30天后再次提示
    localStorage.setItem('pwa-prompt-dismissed', Date.now().toString())
  }

  // 检查是否应该显示提示
  useEffect(() => {
    const dismissed = localStorage.getItem('pwa-prompt-dismissed')
    if (dismissed) {
      const thirtyDays = 30 * 24 * 60 * 60 * 1000
      if (Date.now() - parseInt(dismissed) < thirtyDays) {
        return
      }
    }
  }, [])

  // iOS 检测
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent)

  return (
    <>
      {/* iOS 安装提示 */}
      {isIOS && !window.navigator.standalone && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="fixed bottom-4 left-4 right-4 z-50 md:hidden"
        >
          <div className="bg-black text-white px-4 py-3 rounded-xl shadow-lg flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-sm">
              <span>安装 EduGenius:</span>
              <span className="opacity-80">
                点击
                <svg className="inline-block w-4 h-4 mx-1" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M17.59 15.41L14 12l-3.59 3.41M7 12h10a5 5 0 0 1 5 5v5a5 5 0 0 1-5 5H7a5 5 0 0 1-5-5v-5a5 5 0 0 1 5-5z" />
                </svg>
                分享
              </span>
              </span>
            </div>
            <button
              onClick={() => setShowPrompt(false)}
              className="text-white/80 hover:text-white p-1"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </motion.div>
      )}

      {/* Android/桌面安装提示 */}
      <AnimatePresence>
        {showPrompt && !isIOS && deferredPrompt && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="fixed bottom-4 right-4 z-50"
          >
            <div className="bg-black text-white px-4 py-3 rounded-xl shadow-lg flex items-center gap-3">
              <div className="flex items-center gap-2">
                <Download className="w-4 h-4" />
                <span className="text-sm">安装 EduGenius</span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleInstall}
                  className="px-3 py-1 bg-white text-black rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
                >
                  安装
                </button>
                <button
                  onClick={handleDismiss}
                  className="p-1 text-white/80 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
