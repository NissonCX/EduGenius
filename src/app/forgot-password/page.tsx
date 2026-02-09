'use client'

/**
 * Forgot Password Page - 密码重置请求页面
 */

import { useState } from 'react'
import { motion } from 'framer-motion'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { BookOpen, Loader2, ArrowLeft, Mail, CheckCircle2 } from 'lucide-react'
import { getApiUrl } from '@/lib/config'

export default function ForgotPasswordPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await fetch(getApiUrl('/api/users/password-reset/request'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      })

      if (response.ok) {
        setSuccess(true)
      } else {
        const errorData = await response.json()
        setError(errorData.detail || '请求失败，请稍后重试')
      }
    } catch (err) {
      console.error('Password reset request error:', err)
      setError('网络错误，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-white flex">
      {/* 左侧：信息卡片 */}
      <div className="w-1/2 flex items-center justify-center p-12">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          className="max-w-md"
        >
          <div className="mb-8">
            <Link href="/" className="inline-flex items-center gap-2 text-black">
              <BookOpen className="w-6 h-6" />
              <span className="text-xl font-semibold">EduGenius</span>
            </Link>
          </div>

          <h1 className="text-4xl font-semibold mb-4">
            忘记密码？
          </h1>

          <p className="text-gray-500 text-lg mb-8">
            别担心，输入您的邮箱地址，我们将发送密码重置链接
          </p>

          <Link
            href="/login"
            className="inline-flex items-center gap-2 text-black hover:underline font-medium"
          >
            <ArrowLeft className="w-4 h-4" />
            返回登录
          </Link>
        </motion.div>
      </div>

      {/* 右侧：表单区域 */}
      <div className="w-1/2 flex items-center justify-center p-12 bg-gray-50">
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md"
        >
          {success ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="text-center"
            >
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <CheckCircle2 className="w-8 h-8 text-green-600" />
              </div>

              <h2 className="text-2xl font-semibold mb-4">
                邮件已发送
              </h2>

              <p className="text-gray-600 mb-6">
                我们已向 <span className="font-medium">{email}</span> 发送了密码重置链接。
                请检查您的邮箱并按照说明重置密码。
              </p>

              <p className="text-sm text-gray-500 mb-8">
                没有收到邮件？请检查垃圾邮件文件夹，或稍后再试。
              </p>

              <Link
                href="/login"
                className="inline-block w-full px-6 py-3 bg-black text-white rounded-xl font-medium hover:bg-gray-800 transition-colors text-center"
              >
                返回登录
              </Link>
            </motion.div>
          ) : (
            <>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    邮箱地址
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full pl-12 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent transition-all"
                      placeholder="your@email.com"
                    />
                  </div>
                </div>

                {error && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-3 bg-red-50 border border-red-200 rounded-xl"
                  >
                    <p className="text-sm text-red-700">{error}</p>
                  </motion.div>
                )}

                <motion.button
                  type="submit"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  disabled={loading}
                  className="w-full px-6 py-3 bg-black text-white rounded-xl font-medium hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      发送中...
                    </>
                  ) : (
                    <>
                      <Mail className="w-5 h-5" />
                      发送重置链接
                    </>
                  )}
                </motion.button>
              </form>

              <p className="text-xs text-gray-500 mt-6 text-center">
                我们会发送一封包含重置链接的邮件到您的邮箱
              </p>
            </>
          )}
        </motion.div>
      </div>
    </div>
  )
}
