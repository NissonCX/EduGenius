'use client'

/**
 * ChatMessage - 聊天气泡组件
 * 基于 shadcn/ui 风格的现代化设计
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
      className="group relative px-4 py-6 hover:bg-gray-50/50 transition-colors"
    >
      <div className="max-w-3xl mx-auto">
        <div className={`flex gap-4 ${isUser ? 'flex-row-reverse' : ''}`}>
          {/* 头像 */}
          <div className={`flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center ring-2 ring-white shadow-sm ${
            isUser ? 'bg-gradient-to-br from-indigo-500 to-purple-600' : 'bg-gradient-to-br from-blue-500 to-cyan-500'
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
                <div className="bg-gradient-to-br from-indigo-500 to-purple-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 shadow-sm">
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">
                    {message.content}
                  </p>
                </div>
              ) : (
                /* AI消息 - 优化的 Markdown 渲染 */
                <div className="bg-white rounded-2xl rounded-tl-sm shadow-sm border border-gray-200/60 hover:shadow-md transition-shadow">
                  <div className="p-5">
                    <div className="prose prose-slate prose-sm max-w-none
                                prose-headings:font-bold prose-headings:text-gray-900 prose-headings:scroll-mt-8 prose-headings:scroll-mb-8
                                prose-h1:text-xl prose-h1:mt-8 prose-h1:mb-4
                                prose-h2:text-lg prose-h2:mt-6 prose-h2:mb-3
                                prose-h3:text-base prose-h3:mt-5 prose-h3:mb-3
                                prose-p:leading-relaxed prose-p:text-gray-700 prose-p:text-[15px]
                                prose-p:mb-4
                                prose-strong:text-gray-900 prose-strong:font-semibold
                                prose-em:text-gray-600
                                prose-a:text-indigo-600 prose-a:no-underline hover:prose-a:underline prose-a:font-medium
                                prose-code:font-mono prose-code:text-[13px]
                                prose-code:bg-indigo-50 prose-code:text-indigo-700 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded
                                prose-pre:bg-gray-900 prose-pre:text-gray-100 prose-pre:p-4 prose-pre:rounded-lg prose-pre:my-4
                                prose-pre:prose-code:bg-transparent prose-pre:prose-code:text-gray-100 prose-pre:prose-code:p-0
                                prose-blockquote:not-prose prose-blockquote:border-l-4 prose-blockquote:border-indigo-500 prose-blockquote:bg-indigo-50 prose-blockquote:py-3 prose-blockquote:px-4 prose-blockquote:my-4 prose-blockquote:text-gray-700
                                prose-ul:my-4 prose-ul:space-y-2
                                prose-ol:my-4 prose-ol:space-y-2
                                prose-li:text-gray-700 prose-li:leading-relaxed
                                prose-li:marker:text-indigo-600
                                prose-hr:border-gray-200 prose-hr:my-6">
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
                                  <div className="absolute -top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button
                                      onClick={() => {
                                        const codeText = String(children).replace(/\n$/, '')
                                        navigator.clipboard.writeText(codeText)
                                      }}
                                      className="p-1.5 bg-gray-700 hover:bg-gray-600 rounded-md text-gray-300 hover:text-white transition-colors"
                                      title="复制代码"
                                    >
                                      <Copy className="w-4 h-4" />
                                    </button>
                                  </div>
                                  <div className="bg-gray-900 rounded-lg overflow-hidden shadow-inner">
                                    <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
                                      <span className="text-xs font-medium text-gray-300 font-mono">
                                        {className?.replace('language-', '') || 'code'}
                                      </span>
                                      <span className="text-[10px] text-gray-500">CODE</span>
                                    </div>
                                    <pre className={`${className || ''} p-4 overflow-x-auto`}>
                                      <code className="text-sm font-mono" {...rest}>
                                        {children}
                                      </code>
                                    </pre>
                                  </div>
                                </div>
                              )
                            }

                            // 行内代码
                            return (
                              <code className="font-mono text-[13px]" {...rest}>
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
                            <h3 className="text-base font-semibold mt-4 mb-3 text-gray-900 scroll-mt-8">
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
                              <span className="text-indigo-500 mt-1 flex-shrink-0">•</span>
                              <span className="flex-1">{children}</span>
                            </li>
                          ),
                          // 引用块
                          blockquote: ({ children }) => (
                            <blockquote className="border-l-4 border-indigo-500 bg-indigo-50 py-3 px-4 my-4 text-gray-700 rounded-r-lg">
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
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>
                    </div>
                  </div>

                  {/* AI 操作按钮 */}
                  <div className="flex items-center justify-between px-5 py-3 bg-gray-50 border-t border-gray-200/60 rounded-b-2xl">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={handleCopy}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-200 rounded-lg transition-all cursor-pointer"
                      >
                        {copied ? (
                          <>
                            <Check className="w-3.5 h-3.5 text-green-600" />
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
