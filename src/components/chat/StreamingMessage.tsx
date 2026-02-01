'use client'

/**
 * StreamingMessage - 流式消息组件
 * 使用统一的 LaTeX 处理器，确保与 ChatMessage 一致
 */

import { motion, AnimatePresence } from 'framer-motion'
import { Bot } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import { MermaidInText } from '@/components/visualization/MermaidDiagram'
import { processLatexInMarkdown } from '@/lib/latex-processor'
import 'katex/dist/katex.min.css'

// KaTeX 配置选项
const katexOptions = {
  throwOnError: false,
  errorColor: '#cc0000',
  strict: false,
  trust: false,
  macros: {
    "\\xrightarrow": "\\xrightarrow",
    "\\Delta": "\\Delta",
    "\\text": "\\text"
  }
}

interface StreamingMessageProps {
  content: string
  isComplete?: boolean
}

export function StreamingMessage({ content, isComplete = false }: StreamingMessageProps) {
  // 使用统一的处理函数
  const renderContent = processLatexInMarkdown(content, !isComplete)

  return (
    <div className="group relative px-4 py-6 hover:bg-gray-50/50 transition-colors">
      <div className="max-w-4xl mx-auto">
        <div className="flex gap-4">
          {/* 头像 */}
          <div className="flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center ring-2 ring-white shadow-sm bg-gray-900">
            <Bot className="w-5 h-5 text-white" />
          </div>

          {/* 消息内容 */}
          <div className="flex-1 min-w-0 space-y-2">
            {/* 名称标签 */}
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-900">AI 导师</span>
              <span className="text-xs text-gray-400">正在输入...</span>
            </div>

            {/* 内容 - 使用固定布局避免抖动 */}
            <div className="w-full">
              <div className="bg-white rounded-2xl rounded-tl-sm shadow-sm border border-gray-200 overflow-hidden">
                <div className="p-6 markdown-content min-h-[60px]">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm, remarkMath]}
                    rehypePlugins={[[rehypeKatex, katexOptions]]}
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
                            <div className="my-5">
                              <div className="bg-gray-900 rounded-xl overflow-hidden shadow-lg border border-gray-800">
                                <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
                                  <span className="text-xs font-medium text-gray-300 font-mono">
                                    {className?.replace('language-', '') || 'code'}
                                  </span>
                                  <span className="text-[10px] text-gray-500 uppercase tracking-wide">Code</span>
                                </div>
                                <pre className="p-5 overflow-x-auto">
                                  <code
                                    className={`text-sm font-mono text-gray-100 ${className || ''}`}
                                    {...rest}
                                  >
                                    {children}
                                  </code>
                                </pre>
                              </div>
                            </div>
                          )
                        }

                        // 行内代码
                        return (
                          <code
                            className="font-mono text-[13px] bg-gray-100 text-gray-800 px-1.5 py-0.5 rounded-md"
                            {...rest}
                          >
                            {children}
                          </code>
                        )
                      },

                      // 表格
                      table: ({ children }) => (
                        <div className="my-5 overflow-x-auto rounded-xl border border-gray-200">
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
                        <tbody className="bg-white divide-y divide-gray-100">
                          {children}
                        </tbody>
                      ),
                      tr: ({ children }) => (
                        <tr className="hover:bg-gray-50/80 transition-colors">
                          {children}
                        </tr>
                      ),
                      th: ({ children }) => (
                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                          {children}
                        </th>
                      ),
                      td: ({ children }) => (
                        <td className="px-4 py-3 text-sm text-gray-700">
                          {children}
                        </td>
                      ),

                      // 链接
                      a: ({ children, href }) => (
                        <a
                          href={href}
                          className="text-blue-600 hover:text-blue-700 hover:underline font-medium transition-colors"
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          {children}
                        </a>
                      ),
                    }}
                  >
                    {renderContent}
                  </ReactMarkdown>
                </div>
              </div>
            </div>

            {/* 打字机光标 */}
            <AnimatePresence>
              {!isComplete && (
                <motion.span
                  initial={{ opacity: 1 }}
                  animate={{ opacity: [1, 0, 1] }}
                  exit={{ opacity: 0 }}
                  transition={{
                    duration: 0.8,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                  className="inline-block w-0.5 h-4 bg-black ml-1"
                />
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  )
}
