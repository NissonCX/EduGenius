'use client'

/**
 * ChatMessage - 聊天气泡组件
 * 极简风格，AI 浅灰背景，用户白色背景带边框
 */

import { motion } from 'framer-motion'
import { Bot, User } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import { MermaidInText } from '@/components/visualization/MermaidDiagram'
import 'katex/dist/katex.min.css'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface ChatMessageProps {
  message: Message
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
    >
      {/* 头像 */}
      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
        isUser ? 'bg-black' : 'bg-gray-100'
      }`}>
        {isUser ? (
          <User className="w-5 h-5 text-white" />
        ) : (
          <Bot className="w-5 h-5 text-gray-600" />
        )}
      </div>

      {/* 消息内容 */}
      <div className={`flex-1 max-w-3xl ${isUser ? 'flex justify-end' : ''}`}>
        <div className={`inline-block rounded-2xl p-4 ${
          isUser
            ? 'bg-white border border-gray-200 rounded-tr-sm'
            : 'bg-gray-50 rounded-tl-sm border border-gray-100'
        }`}>
          {/* Markdown 渲染 */}
          {isUser ? (
            <p className="text-sm text-gray-900 whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm, remarkMath]}
                rehypePlugins={[rehypeKatex]}
                components={{
                  // Mermaid 图表渲染
                  code({ node, inline, className, children, ...props }) {
                    const match = /language-mermaid/.exec(className || '')
                    if (!inline && match) {
                      const code = String(children).replace(/\n$/, '')
                      return <MermaidInText code={code} />
                    }

                    // 普通代码块
                    if (!inline) {
                      return (
                        <code className={`${className || ''} block`} {...props}>
                          {children}
                        </code>
                      )
                    }

                    // 行内代码
                    return (
                      <code className="px-1.5 py-0.5 bg-gray-200 rounded text-sm font-mono" {...props}>
                        {children}
                      </code>
                    )
                  },
                  // 其他元素样式
                  p: ({ children }) => <p className="text-gray-900 mb-2">{children}</p>,
                  strong: ({ children }) => <strong className="font-semibold text-black">{children}</strong>,
                  em: ({ children }) => <em className="italic text-gray-700">{children}</em>,
                  ul: ({ children }) => <ul className="list-disc list-inside mb-2">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal list-inside mb-2">{children}</ol>,
                  li: ({ children }) => <li className="mb-1">{children}</li>,
                  h1: ({ children }) => <h1 className="text-lg font-semibold mb-2 text-black">{children}</h1>,
                  h2: ({ children }) => <h2 className="text-base font-semibold mb-2 text-black">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-sm font-semibold mb-2 text-gray-800">{children}</h3>,
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* 时间戳 */}
        <p className={`text-xs text-gray-500 mt-1.5 ${isUser ? 'text-right mr-2' : 'ml-2'}`}>
          {message.timestamp.toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit'
          })}
        </p>
      </div>
    </motion.div>
  )
}
