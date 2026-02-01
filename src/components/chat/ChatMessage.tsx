'use client'

/**
 * ChatMessage - 聊天气泡组件
 * 极简风格，AI 浅灰背景，用户白色背景带边框
 */

import React from 'react'
import { motion } from 'framer-motion'
import { Bot, User } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import { visit } from 'unist-util-visit'
import { MermaidInText } from '@/components/visualization/MermaidDiagram'
import 'katex/dist/katex.min.css'

/**
 * Remark 插件：将代码块从 p 元素中提取出来
 * 解决 <pre> 不能作为 <p> 子元素的 HTML 结构问题
 */
function remarkUnwrapCodeBlocks() {
  return (tree: any) => {
    visit(tree, 'element', (node, index, parent) => {
      // 检查是否是只包含代码块的 p 元素
      if (
        node.tagName === 'p' &&
        node.children &&
        node.children.length === 1 &&
        node.children[0].type === 'element' &&
        node.children[0].tagName === 'pre'
      ) {
        // 将父节点的这个子节点替换为 pre 元素
        if (parent && typeof index === 'number') {
          parent.children[index] = node.children[0]
        }
      }
    })
  }
}

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
          {/* 用户消息：纯文本 */}
          {isUser ? (
            <p className="text-sm text-gray-900 whitespace-pre-wrap">
              {message.content}
            </p>
          ) : (
            /* AI消息：Markdown渲染 */
            <div className="text-sm text-gray-900 max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm, remarkMath, remarkUnwrapCodeBlocks]}
                rehypePlugins={[rehypeKatex]}
                components={{
                  // Mermaid 图表渲染
                  code(props: any) {
                    const { node, inline, className, children, ...rest } = props
                    const match = /language-mermaid/.exec(className || '')
                    if (!inline && match) {
                      const code = String(children).replace(/\n$/, '')
                      return <MermaidInText text={`\`\`\`mermaid\n${code}\n\`\`\``} />
                    }

                    // 代码块
                    if (!inline) {
                      return (
                        <pre className={`${className || ''} bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto my-3`}>
                          <code className="text-sm font-mono block" {...rest}>
                            {children}
                          </code>
                        </pre>
                      )
                    }

                    // 行内代码
                    return (
                      <code className="px-1.5 py-0.5 bg-gray-200 rounded text-sm font-mono text-pink-600" {...rest}>
                        {children}
                      </code>
                    )
                  },
                  p: ({ children }) => <p className="mb-3 leading-7">{children}</p>,
                  strong: ({ children }) => <strong className="font-semibold text-black">{children}</strong>,
                  em: ({ children }) => <em className="italic text-gray-700">{children}</em>,
                  ul: ({ children }) => <ul className="list-disc list-inside mb-4 space-y-1 marker:text-gray-900">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal list-inside mb-4 space-y-1 marker:text-gray-900">{children}</ol>,
                  li: ({ children }) => <li className="mb-1 leading-7">{children}</li>,
                  h1: ({ children }) => <h1 className="text-xl font-bold mb-3 mt-6 text-black pb-2 border-b border-gray-200">{children}</h1>,
                  h2: ({ children }) => <h2 className="text-lg font-bold mb-2 mt-5 text-black">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-base font-bold mb-2 mt-4 text-gray-800">{children}</h3>,
                  h4: ({ children }) => <h4 className="text-sm font-bold mb-2 mt-3 text-gray-800">{children}</h4>,
                  blockquote: ({ children }) => <blockquote className="border-l-4 border-gray-300 pl-4 italic text-gray-600 mb-4">{children}</blockquote>,
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
