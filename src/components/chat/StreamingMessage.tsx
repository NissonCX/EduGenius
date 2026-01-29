'use client'

/**
 * StreamingMessage - 流式消息组件
 * 带有打字机效果的流式消息展示
 */

import { motion, AnimatePresence } from 'framer-motion'
import { Bot } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import { MermaidInText } from '@/components/visualization/MermaidDiagram'
import 'katex/dist/katex.min.css'

interface StreamingMessageProps {
  content: string
  isComplete?: boolean
}

export function StreamingMessage({ content, isComplete = false }: StreamingMessageProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="flex gap-3"
    >
      {/* 头像 */}
      <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 bg-gray-100">
        <Bot className="w-5 h-5 text-gray-600" />
      </div>

      {/* 消息内容 */}
      <div className="flex-1 max-w-3xl">
        <div className="inline-block rounded-2xl p-4 bg-gray-50 rounded-tl-sm border border-gray-100">
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkMath]}
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

                  // 普通代码块
                  if (!inline) {
                    return (
                      <code className={`${className || ''} block`} {...rest}>
                        {children}
                      </code>
                    )
                  }

                  // 行内代码
                  return (
                    <code className="px-1.5 py-0.5 bg-gray-200 rounded text-sm font-mono" {...rest}>
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
              {content}
            </ReactMarkdown>
          </div>

          {/* 打字机光标效果 */}
          <AnimatePresence>
            {!isComplete && (
              <motion.span
                initial={{ opacity: 1 }}
                animate={{ opacity: [1, 0, 1] }}
                exit={{ opacity: 0 }}
                transition={{
                  duration: 0.8,
                  repeat: 1,
                  ease: "easeInOut"
                }}
                className="inline-block w-0.5 h-4 bg-black ml-1 align-middle"
              />
            )}
          </AnimatePresence>
        </div>

        {/* 正在输入提示 */}
        {!isComplete && (
          <p className="text-xs text-gray-500 mt-1.5 ml-2">
            正在输入...
          </p>
        )}
      </div>
    </motion.div>
  )
}
