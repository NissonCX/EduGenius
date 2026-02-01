'use client'

/**
 * StreamingMessage - 流式消息组件
 * 黑白灰极简设计风格
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
      className="group relative px-4 py-6 hover:bg-gray-50 transition-colors"
    >
      <div className="max-w-3xl mx-auto">
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
            <div className="max-w-3xl">
              <div className="bg-white rounded-2xl rounded-tl-sm shadow-sm border border-gray-200">
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
                              <div className="my-4">
                                <div className="bg-gray-900 rounded-lg overflow-hidden shadow-inner border border-gray-800">
                                  <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
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
                          <h1 className="text-xl font-bold mt-6 mb-4 text-gray-900">
                            {children}
                          </h1>
                        ),
                        h2: ({ children }) => (
                          <h2 className="text-lg font-bold mt-5 mb-3 text-gray-900">
                            {children}
                          </h2>
                        ),
                        h3: ({ children }) => (
                          <h3 className="text-base font-semibold mt-4 mb-3 text-gray-800">
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
                        // 段落
                        p: ({ children }) => <p className="mb-4 leading-7 text-[15px] text-gray-700">{children}</p>,
                        strong: ({ children }) => <strong className="font-semibold text-gray-900">{children}</strong>,
                        em: ({ children }) => <em className="italic text-gray-600">{children}</em>,
                      }}
                    >
                      {renderContent}
                    </ReactMarkdown>
                  </div>
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
                  className="inline-block w-0.5 h-4 bg-gray-900 ml-1"
                />
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
