'use client'

/**
 * StreamingMessage - 流式消息组件
 * 优化的 Markdown 渲染，黑白灰极简设计风格
 */

import { motion, AnimatePresence } from 'framer-motion'
import { Bot } from 'lucide-react'
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

/**
 * 修复流式传输时不完整的 Markdown 格式
 */
function fixIncompleteMarkdown(content: string): string {
  let fixed = content

  // 检查未闭合的代码块
  const codeBlockCount = (content.match(/```/g) || []).length
  if (codeBlockCount % 2 !== 0) {
    if (content.length > 50) {
      fixed += '\n```'
    }
  }

  // 检查未闭合的行内代码
  const inlineCodeCount = (content.match(/`/g) || []).length
  if (inlineCodeCount % 2 !== 0) {
    fixed += '`'
  }

  // 检查未闭合的数学公式
  const mathBlockCount = (content.match(/\$\$/g) || []).length
  if (mathBlockCount % 2 !== 0) {
    fixed += '$$'
  }

  return fixed
}

interface StreamingMessageProps {
  content: string
  isComplete?: boolean
}

export function StreamingMessage({ content, isComplete = false }: StreamingMessageProps) {
  const renderContent = isComplete ? content : fixIncompleteMarkdown(content)

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="group relative px-4 py-6 hover:bg-gray-50/50 transition-colors"
    >
      <div className="max-w-4xl mx-auto">
        <div className="flex gap-4">
          {/* 头像 */}
          <div className="flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center ring-2 ring-white shadow-sm bg-gray-900">
            <Bot className="w-5 h-5 text-white" />
          </div>

          {/* 消息内容 */}
          <div className="flex-1 space-y-2">
            {/* 名称标签 */}
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-900">AI 导师</span>
              <span className="text-xs text-gray-400">正在输入...</span>
            </div>

            {/* 内容 */}
            <div className="max-w-4xl">
              <div className="bg-white rounded-2xl rounded-tl-sm shadow-sm border border-gray-200 overflow-hidden">
                <div className="p-6">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm, remarkMath, remarkUnwrapCodeBlocks]}
                    rehypePlugins={[rehypeKatex]}
                    className="prose prose-sm max-w-none
                      prose-headings:font-bold prose-headings:text-gray-900 prose-headings:mt-6 prose-headings:mb-3
                      prose-h1:text-2xl prose-h1:font-bold
                      prose-h2:text-xl prose-h2:font-bold
                      prose-h3:text-lg prose-h3:font-semibold
                      prose-h4:text-base prose-h4:font-semibold
                      prose-p:leading-7 prose-p:text-gray-700 prose-p:text-[15px] prose-p:mb-4
                      prose-strong:text-gray-900 prose-strong:font-semibold
                      prose-em:text-gray-600
                      prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline prose-a:font-medium
                      prose-code:font-mono prose-code:text-[13px] prose-code:bg-gray-100 prose-code:text-gray-800 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded
                      prose-pre:bg-gray-900 prose-pre:text-gray-100 prose-pre:p-4 prose-pre:rounded-lg prose-pre:my-4
                      prose-pre:prose-code:bg-transparent prose-pre:prose-code:text-gray-100 prose-pre:prose-code:p-0
                      prose-blockquote:border-l-4 prose-blockquote:border-gray-300 prose-blockquote:bg-gray-50 prose-blockquote:py-3 prose-blockquote:px-4 prose-blockquote:my-4 prose-blockquote:text-gray-700 prose-blockquote:italic
                      prose-ul:my-4 prose-ul:space-y-2 prose-ul:pl-4
                      prose-ol:my-4 prose-ol:space-y-2 prose-ol:pl-4
                      prose-li:text-gray-700 prose-li:leading-relaxed
                      prose-hr:border-gray-200 prose-hr:my-6"
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
    </motion.div>
  )
}
