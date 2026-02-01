'use client'

/**
 * StreamingMessage - 流式消息组件
 * 基于 shadcn/ui 风格
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
      <div className="max-w-3xl mx-auto">
        <div className="flex gap-4">
          {/* 头像 */}
          <div className="flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center ring-2 ring-white shadow-sm bg-gradient-to-br from-blue-500 to-cyan-500">
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
              <div className="bg-white rounded-2xl rounded-tl-sm shadow-sm border border-gray-200/60">
                <div className="p-5">
                  <div className="prose prose-slate prose-sm max-w-none
                              prose-headings:font-bold prose-headings:text-gray-900 prose-headings:scroll-mt-8
                              prose-h1:text-xl prose-h1:mt-8 prose-h1:mb-4
                              prose-h2:text-lg prose-h2:mt-6 prose-h2:mb-3
                              prose-h3:text-base prose-h3:mt-5 prose-h3:mb-3
                              prose-p:leading-relaxed prose-p:text-gray-700 prose-p:text-[15px] prose-p:mb-4
                              prose-strong:text-gray-900 prose-strong:font-semibold
                              prose-em:text-gray-600
                              prose-a:text-indigo-600 prose-a:no-underline hover:prose-a:underline prose-a:font-medium
                              prose-code:font-mono prose-code:text-[13px]
                              prose-code:bg-indigo-50 prose-code:text-indigo-700
                              prose-pre:bg-gray-900 prose-pre:text-gray-100 prose-pre:p-4 prose-pre:rounded-lg prose-pre:my-4
                              prose-pre:prose-code:bg-transparent prose-pre:prose-code:text-gray-100 prose-pre:prose-code:p-0
                              prose-blockquote:not-prose prose-blockquote:border-l-4 prose-blockquote:border-indigo-500 prose-blockquote:bg-indigo-50
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
                              <div className="my-4">
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
                        // 段落
                        p: ({ children }) => <p className="mb-4 leading-7 text-[15px]">{children}</p>,
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
                  className="inline-block w-0.5 h-4 bg-indigo-500 ml-1"
                />
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
