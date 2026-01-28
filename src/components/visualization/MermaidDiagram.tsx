'use client'

/**
 * MermaidDiagram - Mermaid 图表渲染组件
 * 自动检测并渲染 Mermaid 代码块为可视化图表
 */

import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import mermaid from 'mermaid'

interface MermaidDiagramProps {
  code: string // Mermaid 代码
  className?: string
}

// 初始化 Mermaid（仅一次）
let mermaidInitialized = false

export function MermaidDiagram({ code, className = '' }: MermaidDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [error, setError] = useState<string | null>(null)
  const [svgContent, setSvgContent] = useState<string>('')

  useEffect(() => {
    if (!mermaidInitialized) {
      mermaid.initialize({
        startOnLoad: false,
        theme: 'default',
        securityLevel: 'loose',
        themeVariables: {
          primaryColor: '#000000',
          primaryTextColor: '#111827',
          primaryBorderColor: '#000000',
          lineColor: '#6B7280',
          secondaryColor: '#374151',
          tertiaryColor: '#F3F4F6',
          fontSize: '14px'
        },
        flowchart: {
          useMaxWidth: true,
          htmlLabels: true,
          curve: 'basis'
        }
      })
      mermaidInitialized = true
    }
  }, [])

  useEffect(() => {
    if (!code || !containerRef.current) return

    const renderDiagram = async () => {
      try {
        setError(null)
        // 生成唯一 ID
        const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`

        // 渲染 Mermaid 图表
        const { svg } = await mermaid.render(id, code)
        setSvgContent(svg)
      } catch (err) {
        console.error('Mermaid rendering error:', err)
        setError('图表渲染失败，请检查 Mermaid 语法')
      }
    }

    renderDiagram()
  }, [code])

  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className={`p-4 bg-red-50 border border-red-200 rounded-xl ${className}`}
      >
        <p className="text-sm text-red-600">{error}</p>
      </motion.div>
    )
  }

  if (!svgContent) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-300"></div>
      </div>
    )
  }

  return (
    <motion.div
      ref={containerRef}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className={`my-4 p-4 bg-white border border-gray-200 rounded-xl overflow-x-auto ${className}`}
      dangerouslySetInnerHTML={{ __html: svgContent }}
    />
  )
}

/**
 * 从文本中提取 Mermaid 代码块并渲染
 */
interface MermaidInTextProps {
  text: string
  className?: string
}

export function MermaidInText({ text, className = '' }: MermaidInTextProps) {
  // 正则匹配 ```mermaid ... ``` 代码块
  const mermaidRegex = /```mermaid\n([\s\S]*?)```/g
  const matches = Array.from(text.matchAll(mermaidRegex))

  if (matches.length === 0) {
    // 没有 Mermaid 代码块，直接返回原始文本
    return <div className={className}>{text}</div>
  }

  // 分割文本和 Mermaid 代码块
  const parts: Array<{ type: 'text' | 'mermaid'; content: string }> = []
  let lastIndex = 0

  matches.forEach((match) => {
    // 添加代码块之前的文本
    if (match.index! > lastIndex) {
      parts.push({
        type: 'text',
        content: text.slice(lastIndex, match.index)
      })
    }

    // 添加 Mermaid 代码块
    parts.push({
      type: 'mermaid',
      content: match[1].trim()
    })

    lastIndex = match.index! + match[0].length
  })

  // 添加剩余文本
  if (lastIndex < text.length) {
    parts.push({
      type: 'text',
      content: text.slice(lastIndex)
    })
  }

  return (
    <div className={className}>
      {parts.map((part, index) => {
        if (part.type === 'mermaid') {
          return <MermaidDiagram key={index} code={part.content} />
        }

        // 渲染普通文本（支持 Markdown 基本格式）
        return (
          <div
            key={index}
            className="prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: formatText(part.content) }}
          />
        )
      })}
    </div>
  )
}

/**
 * 简单的文本格式化（支持加粗、代码等基本 Markdown）
 */
function formatText(text: string): string {
  return (
    text
      // 代码块
      .replace(/`([^`]+)`/g, '<code class="px-1.5 py-0.5 bg-gray-100 rounded text-sm font-mono">$1</code>')
      // 加粗
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      // 换行
      .replace(/\n/g, '<br />')
  )
}
