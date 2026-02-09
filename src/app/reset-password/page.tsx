'use client'

/**
 * Reset Password Page - 密码重置确认页面
 */

import { useState, useEffect, Suspense } from 'react'
import { motion } from 'framer-motion'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { BookOpen, Loader2, CheckCircle2, Eye, EyeOff } from 'lucide-react'
import { getApiUrl } from '@/lib/config'

function ResetPasswordForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams.get('token')

  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [verifying, setVerifying] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [tokenValid, setTokenValid] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  // 验证令牌
  useEffect(() => {
    if (!token) {
      setVerifying(false)
      setError('无效的重置链接')
      return
    }

    const verifyToken = async () => {
      try {
        const response = await fetch(getApiUrl('/api/users/password-reset/verify'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token })
        })

        if (response.ok) {
          const data = await response.json()
          if (data.valid) {
            setTokenValid(true)
          } else {
            setError('重置链接已失效或不存在')
          }
        } else {
          setError('验证失败，请重试')
        }
      } catch (err) {
        console.error('Token verification error:', err)
        setError('网络错误，请稍后重试')
      } finally {
        setVerifying(false)
      }
    }

    verifyToken()
  }, [token])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // 验证密码
    if (password.length < 8) {
      setError('密码长度至少为8位')
      return
    }

    if (password !== confirmPassword) {
      setError('两次输入的密码不一致')
      return
    }

    setLoading(true)

    try {
      const response = await fetch(getApiUrl('/api/users/password-reset/confirm'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: password })
      })

      if (response.ok) {
        setSuccess(true)
        // 3秒后跳转到登录页
        setTimeout(() => {
          router.push('/login')
        }, 3000)
      } else {
        const errorData = await response.json()
        setError(errorData.detail || '重置失败，请稍后重试')
      }
    } catch (err) {
      console.error('Password reset error:', err)
      setError('网络错误，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  if (verifying) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-black mx-auto mb-4" />
          <p className="text-gray-600">验证中...</p>
        </div>
      </div>
    )
  }

  if (!tokenValid) {
    return (
      <div className="min-h-screen bg-white flex">
        <div className="w-1/2 flex items-center justify-center p-12">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="max-w-md"
          >
            <div className="mb-8">
              <Link href="/" className="inline-flex items-center gap-2 text-black">
                <BookOpen className="w-6 h-6" />
                <span className="text-xl font-semibold">EduGenius</span>
              </Link>
            </div>

            <h1 className="text-4xl font-semibold mb-4 text-red-600">
              链接无效
            </h1>

            <p className="text-gray-500 text-lg mb-8">
              {error || '此密码重置链接已失效或不存在'}
            </p>

            <Link
              href="/forgot-password"
              className="inline-block px-6 py-3 bg-black text-white rounded-xl font-medium hover:bg-gray-800 transition-colors"
            >
              重新申请重置链接
            </Link>
          </motion.div>
        </div>

        <div className="w-1/2 flex items-center justify-center p-12 bg-gray-50">
          <div className="text-center">
            <p className="text-gray-600 mb-4">请确保：</p>
            <ul className="text-left text-gray-600 space-y-2">
              <li>• 点击了邮件中最新的链接</li>
              <li>• 链接未过期（24小时有效）</li>
              <li>• 链接完整未被截断</li>
            </ul>
          </div>
        </div>
      </div>
    )
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
            设置新密码
          </h1>

          <p className="text-gray-500 text-lg mb-8">
            请输入您的新密码，确保密码足够安全
          </p>

          {success && (
            <Link
              href="/login"
              className="inline-flex items-center gap-2 text-black hover:underline font-medium"
            >
              返回登录
            </Link>
          )}
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
                密码重置成功
              </h2>

              <p className="text-gray-600 mb-6">
                您的密码已成功重置，正在跳转到登录页面...
              </p>
            </motion.div>
          ) : (
            <>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    新密码
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full pr-12 pl-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent transition-all"
                      placeholder="••••••••"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    至少8位，包含大小写字母和数字
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    确认新密码
                  </label>
                  <div className="relative">
                    <input
                      type={showConfirmPassword ? 'text' : 'password'}
                      required
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="w-full pr-12 pl-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent transition-all"
                      placeholder="••••••••"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
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
                      重置中...
                    </>
                  ) : (
                    '重置密码'
                  )}
                </motion.button>
              </form>

              <p className="text-xs text-gray-500 mt-6 text-center">
                重置后，您需要使用新密码登录
              </p>
            </>
          )}
        </motion.div>
      </div>
    </div>
  )
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-white flex items-center justify-center">
        <Loader2 className="w-12 h-12 animate-spin text-black" />
      </div>
    }>
      <ResetPasswordForm />
    </Suspense>
  )
}
