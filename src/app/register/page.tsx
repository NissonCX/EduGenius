'use client'

/**
 * Register Page - 用户注册页面
 * 简化版：直接选择导师风格，无需能力测评
 */

import { useState } from 'react'
import { motion } from 'framer-motion'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { BookOpen, CheckCircle2 } from 'lucide-react'

// 导师风格选项
const TEACHING_STYLES = [
  {
    value: 1,
    name: '温柔',
    description: '耐心细致，用简单的例子和鼓励帮助你理解',
    icon: '🌸',
    color: 'bg-emerald-50 border-emerald-200 hover:border-emerald-400'
  },
  {
    value: 2,
    name: '耐心',
    description: '循序渐进，提供详细的讲解和指导',
    icon: '📗',
    color: 'bg-blue-50 border-blue-200 hover:border-blue-400'
  },
  {
    value: 3,
    name: '标准',
    description: '平衡严谨，既讲清原理又注重应用',
    icon: '📘',
    color: 'bg-purple-50 border-purple-200 hover:border-purple-400'
  },
  {
    value: 4,
    name: '严格',
    description: '注重细节，要求深入理解每一步推理',
    icon: '📙',
    color: 'bg-orange-50 border-orange-200 hover:border-orange-400'
  },
  {
    value: 5,
    name: '严厉',
    description: '挑战思维，培养独立解决问题的能力',
    icon: '🏆',
    color: 'bg-red-50 border-red-200 hover:border-red-400'
  }
]

export default function RegisterPage() {
  const router = useRouter()
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: ''
  })
  const [selectedStyle, setSelectedStyle] = useState<number>(3) // 默认标准
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await fetch('http://localhost:8000/api/users/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          preferred_teaching_style: selectedStyle
        })
      })

      if (response.ok) {
        const result = await response.json()
        // 保存 token 到 localStorage
        localStorage.setItem('token', result.access_token)
        localStorage.setItem('user_id', result.user_id.toString())
        localStorage.setItem('user_email', result.email)
        localStorage.setItem('username', result.username)
        localStorage.setItem('teaching_style', selectedStyle.toString())

        // 注册成功，跳转到学习页面
        router.push('/study')
      } else {
        const errorData = await response.json()
        setError(errorData.detail || '注册失败，请稍后重试')
      }
    } catch (error) {
      console.error('Register error:', error)
      setError('网络错误，请检查连接后重试')
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
            创建你的学习账户
          </h1>

          <p className="text-gray-500 text-lg mb-8">
            选择你喜欢的导师风格，开始个性化学习之旅
          </p>

          {/* 已有账户？ */}
          <p className="text-sm text-gray-500">
            已有账户？
            <Link href="/login" className="text-black font-medium hover:underline ml-1">
              立即登录
            </Link>
          </p>
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
          <form onSubmit={handleRegister} className="space-y-6">
            {/* 基本信息 */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  邮箱
                </label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent transition-all"
                  placeholder="your@email.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  用户名
                </label>
                <input
                  type="text"
                  required
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent transition-all"
                  placeholder="johndoe"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  密码
                </label>
                <input
                  type="password"
                  required
                  minLength={6}
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent transition-all"
                  placeholder="至少6位字符"
                />
              </div>
            </div>

            {/* 选择导师风格 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                选择你喜欢的导师风格
              </label>
              <div className="grid grid-cols-1 gap-3">
                {TEACHING_STYLES.map((style) => (
                  <motion.button
                    key={style.value}
                    type="button"
                    whileHover={{ scale: 1.01 }}
                    whileTap={{ scale: 0.99 }}
                    onClick={() => setSelectedStyle(style.value)}
                    className={`p-4 rounded-xl border-2 text-left transition-all ${
                      selectedStyle === style.value
                        ? 'border-black bg-black text-white'
                        : `${style.color} border-gray-200`
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-2xl">{style.icon}</span>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-semibold">L{style.value}</span>
                          <span className="text-sm font-medium">{style.name}</span>
                          {selectedStyle === style.value && (
                            <CheckCircle2 className="w-4 h-4 ml-auto" />
                          )}
                        </div>
                        <p className={`text-xs ${selectedStyle === style.value ? 'text-gray-300' : 'text-gray-600'}`}>
                          {style.description}
                        </p>
                      </div>
                    </div>
                  </motion.button>
                ))}
              </div>
            </div>

            {/* 错误提示 */}
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm">
                {error}
              </div>
            )}

            {/* 注册按钮 */}
            <motion.button
              type="submit"
              disabled={loading}
              whileHover={{ scale: loading ? 1 : 1.02 }}
              whileTap={{ scale: loading ? 1 : 0.98 }}
              className="w-full px-6 py-3 bg-black text-white rounded-xl font-medium hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? '注册中...' : '创建账户并开始学习'}
            </motion.button>

            <p className="text-xs text-gray-500 text-center">
              注册即表示您同意我们的服务条款和隐私政策
            </p>
          </form>
        </motion.div>
      </div>
    </div>
  )
}
