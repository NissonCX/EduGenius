'use client'

/**
 * ChatMessage - 聊天气泡组件
 * 优化 Markdown 渲染，达到 GPT 级别的展示效果
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

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`py-4 ${isUser ? 'bg-gray-50' : ''}`}
    >
      <div className={`max-w-4xl mx-auto px-4 flex gap-4 ${isUser ? 'flex-row-reverse' : ''}`}>
        {/* 头像 */}
        <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
          isUser ? 'bg-black' : 'bg-gradient-to-br from-blue-500 to-purple-600'
        }`}>
          {isUser ? (
            <User className="w-5 h-5 text-white" />
          ) : (
            <Bot className="w-5 h-5 text-white" />
          )}
        </div>

        {/* 消息内容 */}
        <div className={`flex-1 min-w-0 ${isUser ? 'flex justify-end' : ''}`}>
          <div className={`inline-block max-w-full ${
            isUser
              ? 'bg-black text-white rounded-2xl rounded-tr-sm px-4 py-3'
              : 'text-gray-900'
          }`}>
            {/* 用户消息：纯文本 */}
            {isUser ? (
              <p className="text-sm whitespace-pre-wrap break-words">
                {message.content}
              </p>
            ) : (
              /* AI消息：优化的 Markdown 渲染 */
              <div className="prose prose-slate max-w-none
                          prose-headings:font-semibold prose-headings:text-gray-900
                          prose-headings:mt-6 prose-headings:mb-3
                          prose-h1:text-2xl prose-h1:font-bold
                          prose-h2:text-xl prose-h2:font-bold
                          prose-h3:text-lg prose-h3:font-semibold
                          prose-p:text-gray-800 prose-p:leading-7 prose-p:mb-4
                          prose-p:text-[15px]
                          prose-strong:text-gray-900 prose-strong:font-semibold
                          prose-em:text-gray-700
                          prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline
                          prose-code:text-pink-600 prose-code:bg-pink-50 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:font-mono prose-code:text-sm prose-code:before:content-[''] prose-code:after:content-['']
                          prose-pre:bg-gray-900 prose-pre:text-gray-100 prose-pre:p-4 prose-pre:rounded-lg prose-pre:my-4 prose-pre:shadow-lg
                          prose-pre:prose-code:bg-transparent prose-pre:prose-code:text-gray-100 prose-pre:prose-code:p-0
                          prose-blockquote:border-l-4 prose-blockquote:border-blue-500 prose-blockquote:bg-blue-50 prose-blockquote:py-2 prose-blockquote:px-4 prose-blockquote:my-4 prose-blockquote:italic prose-blockquote:text-gray-700
                          prose-ul:my-4 prose-ul:space-y-2
                          prose-ol:my-4 prose-ol:space-y-2
                          prose-li:text-gray-800 prose-li:leading-relaxed
                          prose-li:marker:text-blue-600
                          prose-hr:border-gray-200 prose-hr:my-6">
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

                      // 代码块 - 增强样式
                      if (!inline) {
                        return (
                          <div className="my-4 group">
                            <div className="flex items-center justify-between bg-gray-900 text-gray-400 text-xs px-3 py-1.5 rounded-t-lg border-b border-gray-700">
                              <span className="font-mono">{className?.replace('language-', '') || 'code'}</span>
                              <span className="opacity-0 group-hover:opacity-100 transition-opacity">代码</span>
                            </div>
                            <pre className={`${className || ''} bg-gray-900 text-gray-100 p-4 rounded-b-lg overflow-x-auto`}>
                              <code className="text-sm font-mono block" {...rest}>
                                {children}
                              </code>
                            </pre>
                          </div>
                        )
                      }

                      // 行内代码 - 优化样式
                      return (
                        <code className="px-1.5 py-0.5 bg-gradient-to-r from-pink-50 to-purple-50 text-pink-600 rounded text-sm font-mono border border-pink-200" {...rest}>
                          {children}
                        </code>
                      )
                    },
                    // 段落 - 优化间距
                    p: ({ children }) => <p className="mb-4 leading-7 text-[15px]">{children}</p>,
                    // 标题 - 增强样式
                    h1: ({ children }) => (
                      <h1 className="text-2xl font-bold mt-6 mb-4 pb-2 border-b border-gray-200 text-gray-900 flex items-center gap-2">
                        <span className="w-1 h-6 bg-blue-600 rounded-full"></span>
                        {children}
                      </h1>
                    ),
                    h2: ({ children }) => (
                      <h2 className="text-xl font-bold mt-5 mb-3 text-gray-900 flex items-center gap-2">
                        <span className="w-1 h-5 bg-blue-500 rounded-full"></span>
                        {children}
                      </h2>
                    ),
                    h3: ({ children }) => (
                      <h3 className="text-lg font-semibold mt-4 mb-3 text-gray-800">
                        {children}
                      </h3>
                    ),
                    h4: ({ children }) => (
                      <h4 className="text-base font-semibold mt-3 mb-2 text-gray-800">
                        {children}
                      </h4>
                    ),
                    // 列表 - 优化样式
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
                      <li className="leading-7 text-gray-800 flex items-start gap-2">
                        <span className="text-blue-600 mt-0.5">•</span>
                        <span className="flex-1">{children}</span>
                      </li>
                    ),
                    // 引用块 - 优化样式
                    blockquote: ({ children }) => (
                      <blockquote className="border-l-4 border-blue-500 bg-blue-50 py-3 px-4 my-4 italic text-gray-700 rounded-r-lg">
                        {children}
                      </blockquote>
                    ),
                    // 表格 - 增强样式
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
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        {children}
                      </th>
                    ),
                    td: ({ children }) => (
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {children}
                      </td>
                    ),
                    // 分隔线
                    hr: () => <hr className="my-6 border-t border-gray-200" />,
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            )}
          </div>

          {/* 时间戳 */}
          <p className={`text-xs text-gray-400 mt-2 ${isUser ? 'text-right' : ''}`}>
            {message.timestamp.toLocaleTimeString('zh-CN', {
              hour: '2-digit',
              minute: '2-digit'
            })}
          </p>
        </div>
      </div>
    </motion.div>
  )
}
