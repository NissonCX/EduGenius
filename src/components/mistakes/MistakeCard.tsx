'use client'

/**
 * MistakeCard - 错题卡片组件
 * 显示单个错题的详细信息
 */

import { useState } from 'react'
import { motion } from 'framer-motion'
import { CheckCircle2, XCircle, BookOpen, Clock, TrendingUp } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'

interface MistakeCardProps {
  question: {
    id: number
    question_text: string
    options?: { [key: string]: string }
    correct_answer: string
    explanation?: string
    user_answer: string
    competency_dimension?: string
    difficulty: number
    chapter_number: number
    chapter_title?: string
    mistake_count: number
  }
  is_mastered: boolean
  onMarkMastered?: (id: number) => void
  onPractice?: (id: number) => void
}

const dimensionNames: Record<string, string> = {
  comprehension: '理解力',
  logic: '逻辑',
  terminology: '术语',
  memory: '记忆',
  application: '应用',
  stability: '稳定性'
}

export function MistakeCard({ question, is_mastered, onMarkMastered, onPractice }: MistakeCardProps) {
  const [showExplanation, setShowExplanation] = useState(false)

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={`bg-white border rounded-xl p-5 hover:shadow-md transition-shadow duration-200 ${
        is_mastered ? 'border-green-200' : 'border-gray-200'
      }`}
    >
      {/* 头部信息 */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className={`inline-block px-2 py-1 text-xs font-medium rounded ${
              is_mastered
                ? 'bg-green-100 text-green-700'
                : 'bg-gray-100 text-gray-700'
            }`}>
              {is_mastered ? '✓ 已掌握' : '待掌握'}
            </span>
            {question.competency_dimension && (
              <span className="inline-block px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded">
                {dimensionNames[question.competency_dimension] || question.competency_dimension}
              </span>
            )}
            <span className="inline-block px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded">
              难度 {'★'.repeat(question.difficulty)}
            </span>
          </div>
          <p className="text-xs text-gray-500">
            第 {question.chapter_number} 章 · 答错 {question.mistake_count} 次
          </p>
        </div>

        {/* 掌握按钮 */}
        {onMarkMastered && !is_mastered && (
          <button
            onClick={() => onMarkMastered(question.id)}
            className="px-3 py-1.5 bg-black text-white text-xs font-medium rounded-lg hover:bg-gray-800 transition-colors"
          >
            标记掌握
          </button>
        )}
      </div>

      {/* 题目内容 */}
      <div className="mb-4">
        <p className="text-sm text-gray-900 leading-relaxed mb-3">{question.question_text}</p>

        {/* 选项（如果是选择题） */}
        {question.options && (
          <div className="space-y-2 mb-3">
            {Object.entries(question.options).map(([key, value]) => (
              <div
                key={key}
                className={`p-3 rounded-lg border ${
                  key === question.correct_answer
                    ? 'border-green-300 bg-green-50'
                    : question.user_answer === key
                    ? 'border-red-300 bg-red-50'
                    : 'border-gray-200'
                }`}
              >
                <span className="font-medium text-gray-700">{key}.</span> {value}
              </div>
            ))}
          </div>
        )}

        {/* 答案信息 */}
        <div className="flex items-center gap-2 text-sm mb-3">
          <span className="text-gray-600">你的答案：</span>
          <span className={`font-medium ${
            question.user_answer === question.correct_answer
              ? 'text-green-600'
              : 'text-red-600'
          }`}>
            {question.user_answer}
          </span>
          <span className="text-gray-400">|</span>
          <span className="text-gray-600">正确答案：</span>
          <span className="font-medium text-green-600">{question.correct_answer}</span>
        </div>

        {/* 解析（可展开） */}
        {question.explanation && (
          <div>
            <button
              onClick={() => setShowExplanation(!showExplanation)}
              className="flex items-center gap-1 text-xs text-gray-600 hover:text-black transition-colors mb-2"
            >
              <BookOpen className="w-3 h-3" />
              {showExplanation ? '隐藏' : '查看'}解析
            </button>

            {showExplanation && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="p-3 bg-gray-50 rounded-lg border border-gray-200"
              >
                <p className="text-sm text-gray-700">
                  <strong className="text-black">解析：</strong>
                  {question.explanation}
                </p>
              </motion.div>
            )}
          </div>
        )}
      </div>

      {/* 操作按钮 */}
      <div className="flex gap-2">
        <button
          onClick={() => onPractice && onPractice(question.id)}
          className="flex-1 px-4 py-2 bg-black text-white text-sm font-medium rounded-lg hover:bg-gray-800 transition-colors flex items-center justify-center gap-2"
        >
          <TrendingUp className="w-4 h-4" />
          专项练习
        </button>
        {is_mastered && (
          <button
            onClick={() => onMarkMastered && onMarkMastered(question.id)}
            className="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition-colors"
          >
            标记未掌握
          </button>
        )}
      </div>
    </motion.div>
  )
}
