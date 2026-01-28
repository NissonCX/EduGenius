'use client'

/**
 * Mistakes Page - 错题本页面
 * 展示所有错题，支持重做和查看解析
 */

import { motion } from 'framer-motion'
import { AlertCircle, RefreshCw, CheckCircle2, TrendingUp } from 'lucide-react'
import Link from 'next/link'

// 模拟错题数据
const mockMistakes = [
  {
    id: 1,
    question: "在数据验证阶段，如果发现无效数据应该怎么做？",
    yourAnswer: "A. 直接忽略",
    correctAnswer: "B. 返回错误并记录日志",
    explanation: "无效数据不应该被忽略，而应该记录日志以便后续分析，这样可以帮助我们发现系统中的问题。",
    category: "数据处理",
    wrongCount: 1,
    mastered: false,
    date: "2024-01-28"
  },
  {
    id: 2,
    question: "矩阵乘法的结合律是什么？",
    yourAnswer: "C. (AB)C = A(BC) 总是成立",
    correctAnswer: "D. (AB)C = A(BC) 在维度匹配时成立",
    explanation: "矩阵乘法满足结合律，但前提是矩阵的维度必须匹配才能进行乘法运算。",
    category: "线性代数",
    wrongCount: 2,
    mastered: false,
    date: "2024-01-27"
  },
  {
    id: 3,
    question: "特征值的几何意义是什么？",
    yourAnswer: "B. 向量的长度",
    correctAnswer: "C. 线性变换的缩放因子",
    explanation: "特征值表示在特征向量方向上，线性变换对向量的缩放程度。",
    category: "线性代数",
    wrongCount: 1,
    mastered: true,
    date: "2024-01-26"
  }
]

export default function MistakesPage() {
  const totalMistakes = mockMistakes.length
  const masteredCount = mockMistakes.filter(m => m.mastered).length
  const needPractice = totalMistakes - masteredCount

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-200 px-8 py-6">
        <div className="max-w-6xl">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
              <AlertCircle className="w-6 h-6 text-red-600" />
            </div>
            <div>
              <h1 className="text-3xl font-semibold">错题本</h1>
              <p className="text-sm text-gray-500 mt-1">
                记录学习过程中的错误，及时复习巩固
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Stats Overview */}
      <section className="px-8 py-6 border-b border-gray-200">
        <div className="max-w-6xl">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-6 bg-red-50 border border-red-200 rounded-2xl"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-red-700">错题总数</p>
                  <p className="text-3xl font-semibold text-red-900 mt-2">{totalMistakes}</p>
                </div>
                <AlertCircle className="w-12 h-12 text-red-300" />
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="p-6 bg-orange-50 border border-orange-200 rounded-2xl"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-orange-700">待巩固</p>
                  <p className="text-3xl font-semibold text-orange-900 mt-2">{needPractice}</p>
                </div>
                <RefreshCw className="w-12 h-12 text-orange-300" />
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="p-6 bg-emerald-50 border border-emerald-200 rounded-2xl"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-emerald-700">已掌握</p>
                  <p className="text-3xl font-semibold text-emerald-900 mt-2">{masteredCount}</p>
                </div>
                <CheckCircle2 className="w-12 h-12 text-emerald-300" />
              </div>
            </motion.div>
          </div>

          {/* 掌握率 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="mt-6 p-4 bg-gradient-to-r from-emerald-50 to-blue-50 border border-gray-200 rounded-xl"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <TrendingUp className="w-5 h-5 text-emerald-600" />
                <span className="text-sm font-medium">错题掌握率</span>
              </div>
              <span className="text-2xl font-semibold text-emerald-600">
                {Math.round((masteredCount / totalMistakes) * 100)}%
              </span>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Mistakes List */}
      <section className="px-8 py-8">
        <div className="max-w-6xl space-y-4">
          <h2 className="text-lg font-semibold mb-6">错题列表</h2>

          {mockMistakes.map((mistake, index) => (
            <motion.div
              key={mistake.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`p-6 border-2 rounded-2xl transition-all hover:shadow-lg ${
                mistake.mastered
                  ? 'bg-emerald-50 border-emerald-200'
                  : 'bg-white border-red-200'
              }`}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-md">
                      {mistake.category}
                    </span>
                    {mistake.mastered && (
                      <span className="px-2 py-1 bg-emerald-100 text-emerald-700 text-xs rounded-md flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" />
                        已掌握
                      </span>
                    )}
                    <span className="text-xs text-gray-500">{mistake.date}</span>
                  </div>
                  <h3 className="text-lg font-medium text-gray-900">{mistake.question}</h3>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-xs text-red-700 mb-1">❌ 你的答案</p>
                  <p className="text-sm text-red-900">{mistake.yourAnswer}</p>
                </div>
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg">
                  <p className="text-xs text-emerald-700 mb-1">✅ 正确答案</p>
                  <p className="text-sm text-emerald-900">{mistake.correctAnswer}</p>
                </div>
              </div>

              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg mb-4">
                <p className="text-xs text-blue-700 mb-2">💡 解析</p>
                <p className="text-sm text-blue-900">{mistake.explanation}</p>
              </div>

              <div className="flex items-center gap-3">
                <button className="px-4 py-2 bg-black text-white text-sm rounded-lg hover:bg-gray-800 transition-colors flex items-center gap-2">
                  <RefreshCw className="w-4 h-4" />
                  重新练习
                </button>
                <Link
                  href="/learn"
                  className="px-4 py-2 bg-gray-100 text-gray-700 text-sm rounded-lg hover:bg-gray-200 transition-colors"
                >
                  返回学习
                </Link>
                {mistake.wrongCount > 1 && (
                  <span className="text-xs text-orange-600 ml-auto">
                    已答错 {mistake.wrongCount} 次
                  </span>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </section>
    </div>
  )
}
