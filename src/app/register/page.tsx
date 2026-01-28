'use client'

/**
 * Register Page - 用户注册页面
 * 带能力测评和 L1-L5 等级选择
 */

import { useState } from 'react'
import { motion } from 'framer-motion'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { ArrowRight, CheckCircle2, Sparkles, BookOpen } from 'lucide-react'

// 能力测评题目
const ASSESSMENT_QUESTIONS = [
  {
    id: 1,
    question: "对于从未接触过的概念，你通常如何学习？",
    options: [
      { text: "需要用日常生活中的例子来比喻", score: 1 },
      { text: "先了解基本定义，再慢慢深入", score: 2 },
      { text: "直接阅读教材，理解原理", score: 3 },
      { text: "查阅相关资料，对比不同观点", score: 4 },
      { text: "直接尝试应用，在实践中理解", score: 5 }
    ]
  },
  {
    id: 2,
    question: "面对一道复杂的数学题，你会：",
    options: [
      { text: "感到困惑，需要详细的解题步骤", score: 1 },
      { text: "尝试按照例题的思路解答", score: 2 },
      { text: "分析题目，选择合适的解题方法", score: 3 },
      { text: "思考多种解法，找出最优方案", score: 4 },
      { text: "快速找到捷径或创新解法", score: 5 }
    ]
  },
  {
    id: 3,
    question: "你更喜欢什么样的学习方式？",
    options: [
      { text: "故事化、形象化的讲解", score: 1 },
      { text: "结构化的知识框架", score: 2 },
      { text: "原理导向的深度解析", score: 3 },
      { text: "案例分析和实际应用", score: 4 },
      { text: "前沿探讨和创新思考", score: 5 }
    ]
  },
  {
    id: 4,
    question: "在学习新知识时，你认为最重要的是：",
    options: [
      { text: "建立直观的理解和感觉", score: 1 },
      { text: "掌握基本的术语和定义", score: 2 },
      { text: "理解原理和内在逻辑", score: 3 },
      { text: "了解适用场景和边界条件", score: 4 },
      { text: "能够创新应用或批判性思考", score: 5 }
    ]
  },
  {
    id: 5,
    question: "如果学习过程中遇到困难，你会：",
    options: [
      { text: "需要大量的鼓励和引导", score: 1 },
      { text: "希望有详细的步骤和提示", score: 2 },
      { text: "能够自己找到解决方案", score: 3 },
      { text: "享受挑战困难的过程", score: 4 },
      { text: "寻求更深入的思考和讨论", score: 5 }
    ]
  }
]

const LEVEL_DESCRIPTIONS = {
  1: { name: "L1 基础", icon: "🌱", color: "bg-emerald-50 border-emerald-200 text-emerald-700" },
  2: { name: "L2 入门", icon: "📗", color: "bg-blue-50 border-blue-200 text-blue-700" },
  3: { name: "L3 进阶", icon: "📘", color: "bg-purple-50 border-purple-200 text-purple-700" },
  4: { name: "L4 高级", icon: "📙", color: "bg-orange-50 border-orange-200 text-orange-700" },
  5: { name: "L5 专家", icon: "🏆", color: "bg-red-50 border-red-200 text-red-700" }
}

export default function RegisterPage() {
  const router = useRouter()
  const [step, setStep] = useState(1) // 1: 注册表单, 2: 能力测评, 3: 结果展示
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: ''
  })
  const [answers, setAnswers] = useState<number[]>([])
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [loading, setLoading] = useState(false)
  const [assessmentResult, setAssessmentResult] = useState<any>(null)
  const [userLevel, setUserLevel] = useState(1)

  // 步骤1：提交注册表单
  const handleRegister = (e: React.FormEvent) => {
    e.preventDefault()
    setStep(2)
  }

  // 步骤2：提交测评答案
  const handleSubmitAssessment = async () => {
    setLoading(true)
    try {
      const response = await fetch('http://localhost:8000/api/users/assess-level', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: formData.email,
          answers: answers
        })
      })

      if (response.ok) {
        const result = await response.json()
        setAssessmentResult(result)
        setUserLevel(result.recommended_level)
        setStep(3)
      }
    } catch (error) {
      console.error('Assessment error:', error)
      // 即使测评失败，也继续到步骤3
      setStep(3)
    } finally {
      setLoading(false)
    }
  }

  // 步骤3：完成注册
  const handleCompleteRegister = async () => {
    setLoading(true)
    try {
      const response = await fetch('http://localhost:8000/api/users/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          cognitive_level: userLevel
        })
      })

      if (response.ok) {
        // 注册成功，跳转到学习页面
        router.push('/study')
      } else {
        const error = await response.json()
        alert(`注册失败: ${error.detail}`)
      }
    } catch (error) {
      console.error('Register error:', error)
      alert('注册失败，请稍后重试')
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
            {step === 1 && '创建你的学习账户'}
            {step === 2 && '能力测评'}
            {step === 3 && '准备开始学习'}
          </h1>

          <p className="text-gray-500 text-lg mb-8">
            {step === 1 && '加入我们，开始你的个性化学习之旅'}
            {step === 2 && '让我们了解你的学习风格和水平'}
            {step === 3 && '一切就绪，即将开始'}
          </p>

          {/* 步骤指示器 */}
          <div className="flex items-center gap-3 mb-8">
            {[1, 2, 3].map((s) => (
              <div key={s} className="flex items-center gap-2">
                <motion.div
                  className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold ${
                    s <= step ? 'bg-black text-white' : 'bg-gray-100 text-gray-400'
                  }`}
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: s * 0.1 }}
                >
                  {s}
                </motion.div>
                {s < 3 && (
                  <div className={`w-8 h-0.5 ${s < step ? 'bg-black' : 'bg-gray-200'}`} />
                )}
              </div>
            ))}
          </div>

          {/* 等级展示 */}
          {step === 3 && assessmentResult && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`p-6 rounded-2xl border-2 ${LEVEL_DESCRIPTIONS[userLevel].color} mb-6`}
            >
              <div className="text-center">
                <div className="text-4xl mb-2">{LEVEL_DESCRIPTIONS[userLevel].icon}</div>
                <h3 className="text-2xl font-semibold mb-2">{LEVEL_DESCRIPTIONS[userLevel].name}</h3>
                <p className="text-sm opacity-80 mb-4">
                  根据测评结果，我们推荐从这个等级开始
                </p>
                <div className="flex items-center justify-center gap-2 text-sm">
                  <span>测评得分：</span>
                  <span className="font-semibold">{assessmentResult.avg_score.toFixed(1)}</span>
                </div>
              </div>
            </motion.div>
          )}

          {/* 已有账户？ */}
          {step === 1 && (
            <p className="text-sm text-gray-500">
              已有账户？
              <Link href="/login" className="text-black font-medium hover:underline ml-1">
                立即登录
              </Link>
            </p>
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
          {/* 步骤1：注册表单 */}
          {step === 1 && (
            <form onSubmit={handleRegister} className="space-y-4">
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
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent transition-all"
                  placeholder="•••••••••"
                />
              </div>

              <motion.button
                type="submit"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="w-full px-6 py-3 bg-black text-white rounded-xl font-medium hover:bg-gray-800 transition-colors flex items-center justify-center gap-2"
              >
                下一步
                <ArrowRight className="w-5 h-5" />
              </motion.button>
            </form>
          )}

          {/* 步骤2：能力测评 */}
          {step === 2 && (
            <div className="space-y-6">
              <div className="text-center mb-6">
                <Sparkles className="w-12 h-12 mx-auto mb-4 text-emerald-600" />
                <p className="text-gray-600">
                  请根据你的真实情况回答以下问题
                </p>
              </div>

              {/* 进度条 */}
              <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-black rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${((currentQuestion + 1) / ASSESSMENT_QUESTIONS.length) * 100}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>

              <div className="text-center text-sm text-gray-500 mb-4">
                问题 {currentQuestion + 1} / {ASSESSMENT_QUESTIONS.length}
              </div>

              {/* 问题卡片 */}
              <motion.div
                key={currentQuestion}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="bg-white p-6 rounded-2xl border border-gray-200"
              >
                <h3 className="text-lg font-semibold mb-6 text-center">
                  {ASSESSMENT_QUESTIONS[currentQuestion].question}
                </h3>

                <div className="space-y-3">
                  {ASSESSMENT_QUESTIONS[currentQuestion].options.map((option, index) => (
                    <motion.button
                      key={index}
                      whileHover={{ scale: 1.01, x: 4 }}
                      whileTap={{ scale: 0.99 }}
                      onClick={() => {
                        const newAnswers = [...answers]
                        newAnswers[currentQuestion] = option.score
                        setAnswers(newAnswers)

                        if (currentQuestion < ASSESSMENT_QUESTIONS.length - 1) {
                          setCurrentQuestion(currentQuestion + 1)
                        } else {
                          handleSubmitAssessment()
                        }
                      }}
                      className={`w-full p-4 rounded-xl border text-left transition-all ${
                        answers[currentQuestion] === option.score
                          ? 'bg-black text-white border-black'
                          : 'bg-white border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <span className="flex-shrink-0 w-6 h-6 rounded-full border flex items-center justify-center text-xs">
                          {String.fromCharCode(65 + index)}
                        </span>
                        <span className="flex-1">{option.text}</span>
                        {answers[currentQuestion] === option.score && (
                          <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
                        )}
                      </div>
                    </motion.button>
                  ))}
                </div>
              </motion.div>
            </div>
          )}

          {/* 步骤3：完成注册 */}
          {step === 3 && (
            <div className="space-y-6 text-center">
              <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle2 className="w-8 h-8 text-emerald-600" />
              </div>

              <h3 className="text-2xl font-semibold mb-2">
                准备就绪！
              </h3>

              <p className="text-gray-600 mb-6">
                你的账户已创建完成，推荐等级：{assessmentResult?.level_name}
              </p>

              <motion.button
                onClick={handleCompleteRegister}
                disabled={loading}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="w-full px-6 py-3 bg-black text-white rounded-xl font-medium hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
              >
                {loading ? '注册中...' : '开始学习'}
                <Sparkles className="w-5 h-5" />
              </motion.button>

              <p className="text-xs text-gray-500">
                注册即表示您同意我们的服务条款和隐私政策
              </p>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  )
}
