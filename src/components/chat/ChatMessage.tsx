'use client'

/**
 * ChatMessage - 聊天气泡组件
 * 黑白灰极简设计风格
 */

import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Bot, User, Copy, Check } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import { visit } from 'unist-util-visit'
import { MermaidInText } from '@/components/visualization/MermaidDiagram'
import 'katex/dist/katex.min.css'

/**
 * Remark 插件：将代码块从 p 元素中提取出来
 */
function remarkUnwrapCodeBlocks() {
  return (tree: any) => {
    visit(tree, 'element', (node, index, parent) => {
      if (
        node.tagName === 'p' &&
        node.children &&
        node.children.length === 1 &&
        node.children[0].type === 'element' &&
        node.children[0].tagName === 'pre'
      ) {
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
  const [copied, setCopied] = React.useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.2 }}
      className="group relative px-4 py-6 hover:bg-gray-50 transition-colors"
    >
      <div className="max-w-3xl mx-auto">
        <div className={`flex gap-4 ${isUser ? 'flex-row-reverse' : ''}`}>
          {/* 头像 */}
          <div className={`flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center ring-2 ring-white shadow-sm ${
            isUser ? 'bg-black' : 'bg-gray-900'
          }`}>
            {isUser ? (
              <User className="w-5 h-5 text-white" />
            ) : (
              <Bot className="w-5 h-5 text-white" />
            )}
          </div>

          {/* 消息内容 */}
          <div className={`flex-1 min-w-0 space-y-2`}>
            {/* 名称标签 */}
            <div className={`flex items-center gap-2 ${isUser ? 'justify-end' : ''}`}>
              <span className="text-sm font-medium text-gray-900">
                {isUser ? '你' : 'AI 导师'}
              </span>
              <span className="text-xs text-gray-400">
                {message.timestamp.toLocaleTimeString('zh-CN', {
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </span>
            </div>

            {/* 内容 */}
            <div className={`relative ${
              isUser
                ? 'ml-auto max-w-2xl'
                : 'max-w-3xl'
            }`}>
              {/* 用户消息 */}
              {isUser ? (
                <div className="bg-black text-white rounded-2xl rounded-tr-sm px-4 py-3 shadow-sm">
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">
                    {message.content}
                  </p>
                </div>
              ) : (
                /* AI消息 - 优化的 Markdown 渲染 */
                <div className="bg-white rounded-2xl rounded-tl-sm shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
                  <div className="p-5">
                    <div className="prose prose-sm max-w-none">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm, remarkMath, remarkUnwrapCodeBlocks]}
                        rehypePlugins={[rehypeKatex]}
                        components={{
                          // Mermaid 图表
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
                                <div className="group relative my-4">
                                  <div className="absolute -top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                                    <button
                                      onClick={() => {
                                        const codeText = String(children).replace(/\n$/, '')
                                        navigator.clipboard.writeText(codeText)
                                      }}
                                      className="p-1.5 bg-gray-800 hover:bg-gray-700 rounded-md text-gray-200 hover:text-white transition-colors shadow-sm"
                                      title="复制代码"
                                    >
                                      <Copy className="w-4 h-4" />
                                    </button>
                                  </div>
                                  <div className="bg-gray-900 rounded-lg overflow-hidden shadow-lg border border-gray-800">
                                    <div className="flex items-center justify-between px-4 py-2 bg-gray-800/90 border-b border-gray-700">
                                      <span className="text-xs font-medium text-gray-300 font-mono">
                                        {className?.replace('language-', '') || 'code'}
                                      </span>
                                      <span className="text-[10px] text-gray-500">CODE</span>
                                    </div>
                                    <pre className={`${className || ''} p-4 overflow-x-auto`}>
                                      <code className="text-sm font-mono text-gray-100" {...rest}>
                                        {children}
                                      </code>
                                    </pre>
                                  </div>
                                </div>
                              )
                            }

                            // 行内代码
                            return (
                              <code className="font-mono text-[13px] bg-gray-100 text-gray-800 px-1.5 py-0.5 rounded" {...rest}>
                                {children}
                              </code>
                            )
                          },
                          // 标题
                          h1: ({ children }) => (
                            <h1 className="text-xl font-bold mt-6 mb-4 text-gray-900 scroll-mt-8">
                              {children}
                            </h1>
                          ),
                          h2: ({ children }) => (
                            <h2 className="text-lg font-bold mt-5 mb-3 text-gray-900 scroll-mt-8">
                              {children}
                            </h2>
                          ),
                          h3: ({ children }) => (
                            <h3 className="text-base font-semibold mt-4 mb-3 text-gray-800 scroll-mt-8">
                              {children}
                            </h3>
                          ),
                          // 列表
                          ul: ({ children }) => (
                            <ul className="my-4 space-y-2">
                              {children}
                            </ul>
                          ),
                          ol: ({ children }) => (
                            <ol className="my-4 space-y-2">
                              {children}
                            </ol>
                          ),
                          li: ({ children }) => (
                            <li className="leading-relaxed text-gray-700 flex items-start gap-2">
                              <span className="text-gray-900 mt-1 flex-shrink-0">•</span>
                              <span className="flex-1">{children}</span>
                            </li>
                          ),
                          // 引用块
                          blockquote: ({ children }) => (
                            <blockquote className="border-l-4 border-gray-300 bg-gray-50 py-3 px-4 my-4 text-gray-700 rounded-r-lg">
                              {children}
                            </blockquote>
                          ),
                          // 表格
                          table: ({ children }) => (
                            <div className="my-4 overflow-x-auto rounded-lg border border-gray-200">
                              <table className="min-w-full divide-y divide-gray-200">
                                {children}
                              </table>
                            </div>
                          ),
                          thead: ({ children }) => (
                            <thead className="bg-gray-50">
                              {children}
                            </thead>
                          ),
                          tbody: ({ children }) => (
                            <tbody className="bg-white divide-y divide-gray-200">
                              {children}
                            </tbody>
                          ),
                          tr: ({ children }) => (
                            <tr className="hover:bg-gray-50 transition-colors">
                              {children}
                            </tr>
                          ),
                          th: ({ children }) => (
                            <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                              {children}
                            </th>
                          ),
                          td: ({ children }) => (
                            <td className="px-4 py-2 text-sm text-gray-700">
                              {children}
                            </td>
                          ),
                          // 段落
                          p: ({ children }) => <p className="mb-4 leading-7 text-[15px] text-gray-700">{children}</p>,
                          strong: ({ children }) => <strong className="font-semibold text-gray-900">{children}</strong>,
                          em: ({ children }) => <em className="italic text-gray-600">{children}</em>,
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>
                    </div>
                  </div>

                  {/* AI 操作按钮 */}
                  <div className="flex items-center justify-between px-5 py-3 bg-gray-50 border-t border-gray-200 rounded-b-2xl">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={handleCopy}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-200 rounded-lg transition-all cursor-pointer"
                      >
                        {copied ? (
                          <>
                            <Check className="w-3.5 h-3.5 text-gray-600" />
                            <span>已复制</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3.5 h-3.5" />
                            <span>复制</span>
                          </>
                        )}
                      </button>
                    </div>
                    <span className="text-xs text-gray-500">
                      AI 生成内容
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
