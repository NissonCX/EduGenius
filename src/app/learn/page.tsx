'use client'

/**
 * Learn Page - 学习界面示例
 * 集成所有第五阶段的互动组件
 */

import { useState } from 'react'
import { motion } from 'framer-motion'
import { SidebarEnhanced } from '@/components/layout/SidebarEnhanced'
import { AnimatedProgressBar } from '@/components/progress/AnimatedProgressBar'
import { MermaidInText } from '@/components/visualization/MermaidDiagram'
import { ArrowRight, Check, X, Lightbulb } from 'lucide-react'

export default function LearnPage() {
  const [progress, setProgress] = useState(65)
  const [triggerAnimation, setTriggerAnimation] = useState(false)
  const [strictnessLevel, setStrictnessLevel] = useState(3)
  const [errorTrigger, setErrorTrigger] = useState(0)

  // 模拟 AI 回复（包含 Mermaid 代码块）
  const aiResponse = `很好的问题！让我用流程图来解释这个概念：

\`\`\`mermaid
graph TD
    A[输入数据] --> B{数据验证}
    B -->|有效| C[处理数据]
    B -->|无效| D[返回错误]
    C --> E[保存结果]
    E --> F[返回成功]
    D --> G[记录日志]
\`\`\`

从上面的流程图可以看出，整个过程包含数据验证、处理和结果反馈三个关键环节。

**要点总结**：
1. 数据验证是第一步，确保输入的合法性
2. 处理数据时要考虑边界条件
3. 保存结果前需要再次检查

接下来我们看一个更复杂的例子...`

  // 模拟题目
  const currentQuestion = {
    id: 1,
    text: "在数据验证阶段，如果发现无效数据应该怎么做？",
    options: [
      "A. 直接忽略",
      "B. 返回错误并记录日志",
      "C. 继续处理",
      "D. 修改数据"
    ]
  }

  const handleAnswer = (correct: boolean) => {
    if (correct) {
      // 答对：触发流光动画
      setProgress(prev => Math.min(100, prev + 5))
      setTriggerAnimation(true)
      setTimeout(() => setTriggerAnimation(false), 1600)
    } else {
      // 答错：触发错题本动画
      setErrorTrigger(prev => prev + 1)
    }
  }

  return (
    <div className="flex min-h-screen bg-white">
      {/* 增强侧边栏 */}
      <SidebarEnhanced
        onErrorTrigger={() => {}}
        onStrictnessChange={(level) => setStrictnessLevel(level)}
      />

      {/* 主内容区 */}
      <div className="flex-1 flex flex-col">
        {/* 顶部进度条 */}
        <header className="border-b border-gray-200 px-8 py-6">
          <div className="max-w-4xl">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h1 className="text-2xl font-semibold">第三章：矩阵运算</h1>
                <p className="text-sm text-gray-500 mt-1">
                  认知等级：<span className="font-medium">L{strictnessLevel}</span>
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-500">当前进度</p>
                <p className="text-2xl font-semibold text-emerald-600">{progress}%</p>
              </div>
            </div>

            {/* 带流光效果的进度条 */}
            <AnimatedProgressBar
              value={progress}
              triggerAnimation={triggerAnimation}
              height="12px"
            />
          </div>
        </header>

        {/* 主内容 */}
        <main className="flex-1 overflow-y-auto px-8 py-8">
          <div className="max-w-4xl space-y-8">
            {/* AI 讲解区域（包含 Mermaid 图表） */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-6 bg-white border border-gray-200 rounded-2xl"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                  <Lightbulb className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h2 className="font-semibold">AI 导师讲解</h2>
                  <p className="text-xs text-gray-500">
                    风格：{strictnessLevel <= 2 ? '温柔引导' : strictnessLevel === 3 ? '标准教学' : '严格要求'}
                  </p>
                </div>
              </div>

              {/* 渲染包含 Mermaid 的文本 */}
              <div className="prose prose-sm max-w-none">
                <MermaidInText text={aiResponse} />
              </div>
            </motion.section>

            {/* 测试题区域 */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="p-6 bg-gray-50 border border-gray-200 rounded-2xl"
            >
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-black text-white text-xs flex items-center justify-center">
                  ?
                </span>
                测试题
              </h3>

              <p className="text-sm text-gray-700 mb-6">{currentQuestion.text}</p>

              <div className="space-y-3">
                {currentQuestion.options.map((option, index) => (
                  <motion.button
                    key={index}
                    whileHover={{ scale: 1.01, x: 4 }}
                    whileTap={{ scale: 0.99 }}
                    onClick={() => handleAnswer(index === 1)} // 假设 B 是正确答案
                    className="w-full flex items-center gap-4 p-4 bg-white border border-gray-200 rounded-xl hover:border-gray-300 hover:shadow-sm transition-all text-left group"
                  >
                    <span className="w-8 h-8 rounded-full bg-gray-100 group-hover:bg-black group-hover:text-white transition-colors flex items-center justify-center text-sm font-medium">
                      {String.fromCharCode(65 + index)}
                    </span>
                    <span className="flex-1">{option.slice(2)}</span>
                    <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-black transition-colors" />
                  </motion.button>
                ))}
              </div>

              {/* 提示信息 */}
              <div className="mt-6 p-4 bg-blue-50 border border-blue-100 rounded-xl">
                <p className="text-xs text-blue-700">
                  💡 提示：点击选项提交答案，答对进度会增长，答错会自动加入错题本
                </p>
              </div>
            </motion.section>

            {/* 交互反馈示例 */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="grid grid-cols-2 gap-4"
            >
              {/* 答对反馈 */}
              <div className="p-6 bg-emerald-50 border border-emerald-200 rounded-2xl">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-8 h-8 rounded-full bg-emerald-500 flex items-center justify-center">
                    <Check className="w-5 h-5 text-white" />
                  </div>
                  <span className="font-medium text-emerald-900">答对效果</span>
                </div>
                <p className="text-xs text-emerald-700">
                  进度条产生流光增长动画，百分比数字放大跳动
                </p>
                <button
                  onClick={() => handleAnswer(true)}
                  className="mt-4 px-4 py-2 bg-emerald-500 text-white text-sm rounded-lg hover:bg-emerald-600 transition-colors"
                >
                  测试答对效果
                </button>
              </div>

              {/* 答错反馈 */}
              <div className="p-6 bg-red-50 border border-red-200 rounded-2xl">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-8 h-8 rounded-full bg-red-500 flex items-center justify-center">
                    <X className="w-5 h-5 text-white" />
                  </div>
                  <span className="font-medium text-red-900">答错效果</span>
                </div>
                <p className="text-xs text-red-700">
                  侧边栏错题本图标微颤，数字 +1
                </p>
                <button
                  onClick={() => handleAnswer(false)}
                  className="mt-4 px-4 py-2 bg-red-500 text-white text-sm rounded-lg hover:bg-red-600 transition-colors"
                >
                  测试答错效果
                </button>
              </div>
            </motion.section>

            {/* 使用说明 */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="p-6 bg-gradient-to-r from-blue-50 to-purple-50 border border-gray-200 rounded-2xl"
            >
              <h3 className="font-semibold mb-4">✨ 互动功能演示</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div className="space-y-2">
                  <p className="font-medium text-gray-900">1. 进度条流光效果</p>
                  <p className="text-gray-600">答对题目时，进度条会产生流光增长动画，百分比数字放大跳动</p>
                </div>
                <div className="space-y-2">
                  <p className="font-medium text-gray-900">2. 错题本微颤</p>
                  <p className="text-gray-600">答错题目时，侧边栏错题本图标会微颤，红点数字增加</p>
                </div>
                <div className="space-y-2">
                  <p className="font-medium text-gray-900">3. Mermaid 图表</p>
                  <p className="text-gray-600">AI 回复中的 Mermaid 代码块自动渲染为可视化流程图</p>
                </div>
                <div className="space-y-2">
                  <p className="font-medium text-gray-900">4. 严厉程度调节</p>
                  <p className="text-gray-600">侧边栏滑块实时调节导师风格，影响后续对话语气</p>
                </div>
              </div>
            </motion.section>
          </div>
        </main>
      </div>
    </div>
  )
}
