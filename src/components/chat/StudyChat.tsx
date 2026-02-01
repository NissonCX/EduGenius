'use client'

/**
 * StudyChat - 沉浸式学习对话组件
 * 支持 SSE 流式传输、打字机效果、Markdown 渲染
 * 支持会话恢复和历史记录加载
 */

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Loader2 } from 'lucide-react'
import { Message } from '@/types/chat'
import { ChatMessage } from './ChatMessage'
import { StreamingMessage } from './StreamingMessage'
import { TypingIndicator } from './TypingIndicator'
import { safeFetch, handleApiError, getFriendlyErrorMessage } from '@/lib/errors'
import { getApiUrl, getAuthHeadersSimple } from '@/lib/config'

interface Subsection {
  subsection_number: string
  subsection_title: string
  page_number?: number
  completion_percentage: number
}

interface StudyChatProps {
  chapterId?: string
  chapterTitle?: string
  subsectionId?: string  // 新增：小节ID
  subsectionTitle?: string  // 新增：小节标题
  documentId?: number  // 新增：文档ID
  teachingStyle?: number  // 新增：教学风格
  className?: string
}

export function StudyChat({
  chapterId = '1',
  chapterTitle = '第一章：线性代数基础',
  subsectionId,
  subsectionTitle,
  documentId,
  teachingStyle = 3,  // 新增：教学风格 prop，默认 L3
  className = ''
}: StudyChatProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')

  // 用户信息状态（避免 hydration 问题）
  const [userId, setUserId] = useState<number | null>(null)
  const [currentStyle, setCurrentStyle] = useState<number>(teachingStyle)  // 使用 prop 作为初始值
  const [isLoadingHistory, setIsLoadingHistory] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // 初始化用户信息和教学风格（仅客户端）
  useEffect(() => {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      try {
        const user = JSON.parse(userStr)
        if (user?.id) {
          setUserId(user.id)
        }
      } catch {
        // 忽略解析错误
      }
    }
  }, [])

  // 监听 teachingStyle prop 的变化（从父组件传入）
  useEffect(() => {
    if (teachingStyle && teachingStyle !== currentStyle) {
      console.log(`[StudyChat] 教学风格更新: L${currentStyle} → L${teachingStyle}`)
      setCurrentStyle(teachingStyle)
    }
  }, [teachingStyle])

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  // 更新学习进度（后端已自动保存对话，前端只需更新进度）
  const updateLearningProgress = async () => {
    if (!userId) return

    try {
      // 更新学习进度（增加1分钟学习时间）
      await fetch(getApiUrl(`/api/users/${userId}/update-chapter-progress`), {
        method: 'POST',
        headers: getAuthHeadersSimple(),
        body: JSON.stringify({
          document_id: documentId || 1,
          chapter_number: parseInt(chapterId, 10),
          chapter_title: chapterTitle,
          time_spent_minutes: 1,
          completion_percentage: null // 让后端自动计算
        })
      })
    } catch (error) {
      console.error('更新学习进度失败:', error)
      // 不影响用户体验
    }
  }

  // 加载历史对话和用户状态
  useEffect(() => {
    let isMounted = true // 防止组件卸载后更新状态
    const abortController = new AbortController() // 取消请求

    const loadHistory = async () => {
      if (!userId) {
        setIsLoadingHistory(false)
        return
      }

      const historyUrl = getApiUrl(`/api/users/${userId}/history?chapter_number=${chapterId}`)
      console.log(`[StudyChat] 加载历史记录: ${historyUrl}`)

      try {
        const historyResponse = await safeFetch(
          historyUrl,
          {
            headers: getAuthHeadersSimple(),
            signal: abortController.signal
          }
        )

        if (historyResponse.ok && isMounted) {
          const historyData = await historyResponse.json()
          console.log('[StudyChat] 历史记录响应:', historyData)

          // 转换历史对话为 Message 格式
          const historyMessages: Message[] = historyData.conversations.map((conv: any) => ({
            id: conv.id.toString(),
            role: conv.role as 'user' | 'assistant',
            content: conv.content,
            timestamp: new Date(conv.created_at)
          }))

          // 如果没有历史记录，显示欢迎消息
          if (historyMessages.length === 0) {
            // 构建欢迎消息，包含小节信息（如果有）
            let welcomeContent = `👋 欢迎来到 **${chapterTitle}**！\n\n`

            if (subsectionTitle) {
              welcomeContent += `当前学习小节：**${subsectionId} ${subsectionTitle}**\n\n`
            }

            welcomeContent += `我是你的 AI 导师。今天我们将一起探索这个章节的核心概念。\n\n让我们开始吧！请告诉我你想了解的内容，或者我可以为你讲解重点知识。`

            historyMessages.push({
              id: 'welcome',
              role: 'assistant',
              content: welcomeContent,
              timestamp: new Date()
            })
          }

          if (isMounted) {
            setMessages(historyMessages)
          }

        } else if (isMounted) {
          // API 失败，显示默认欢迎消息
          let welcomeContent = `👋 欢迎来到 **${chapterTitle}**！\n\n`

          if (subsectionTitle) {
            welcomeContent += `当前学习小节：**${subsectionId} ${subsectionTitle}**\n\n`
          }

          welcomeContent += `我是你的 AI 导师。今天我们将一起探索这个章节的核心概念。\n\n让我们开始吧！请告诉我你想了解的内容，或者我可以为你讲解重点知识。`

          setMessages([{
            id: 'welcome',
            role: 'assistant',
            content: welcomeContent,
            timestamp: new Date()
          }])
        }
      } catch (error: any) {
        if (error.name === 'AbortError') {
          console.log('请求已取消')
          return
        }

        // 尝试序列化错误对象以便查看
        console.error('原始错误对象:', error)
        console.error('错误类型:', typeof error)
        console.error('错误构造函数:', error?.constructor?.name)
        console.error('错误键:', Object.keys(error || {}))

        const apiError = handleApiError(error)

        // 使用 JSON.stringify 确保能看到完整内容
        console.error('加载历史失败，错误详情:', JSON.stringify({
          message: apiError.message,
          status: apiError.status,
          code: apiError.code,
          details: apiError.details
        }, null, 2))

        // 如果是认证错误，不显示欢迎消息
        if (apiError.status === 401) {
          console.warn('用户未登录，跳过历史记录加载')
          if (isMounted) {
            setIsLoadingHistory(false)
          }
          return
        }

        // 显示默认欢迎消息
        if (isMounted) {
          let welcomeContent = `👋 欢迎来到 **${chapterTitle}**！\n\n`

          if (subsectionTitle) {
            welcomeContent += `当前学习小节：**${subsectionId} ${subsectionTitle}**\n\n`
          }

          welcomeContent += `我是你的 AI 导师。今天我们将一起探索这个章节的核心概念。\n\n让我们开始吧！请告诉我你想了解的内容，或者我可以为你讲解重点知识。`

          setMessages([{
            id: 'welcome',
            role: 'assistant',
            content: welcomeContent,
            timestamp: new Date()
          }])
        }
      } finally {
        if (isMounted) {
          setIsLoadingHistory(false)
        }
      }
    }

    loadHistory()

    // 清理函数
    return () => {
      isMounted = false
      abortController.abort()
    }
  }, [chapterId, chapterTitle, userId])

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingContent])

  // SSE 流式响应（优化版）
  const startStreaming = async (userMessage: string) => {
    setIsStreaming(true)
    setStreamingContent('')

    const abortController = new AbortController()

    console.log(`[StudyChat] 发送消息，使用教学风格: L${currentStyle}`)

    try {
      const response = await safeFetch(getApiUrl('/api/teaching/chat'), {
        method: 'POST',
        headers: getAuthHeadersSimple(),
        body: JSON.stringify({
          message: userMessage,
          chapter_id: chapterId,
          student_level: currentStyle,
          stream: true,
          user_id: userId,
          document_id: documentId,
          subsection_id: subsectionId,
          subsection_title: subsectionTitle
        }),
        signal: abortController.signal
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) throw new Error('No reader available')

      let buffer = ''
      let fullContent = ''
      let chunkCount = 0
      const startTime = Date.now()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.trim() === '') continue
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim()
            if (data === '[DONE]') continue

            try {
              const parsed = JSON.parse(data)

              // 处理不同类型的 SSE 数据
              if (parsed.content) {
                chunkCount++
                fullContent += parsed.content

                // 打字机效果：逐字符累积
                setStreamingContent(fullContent)

                // 调试日志（开发时使用）
                if (process.env.NODE_ENV === 'development') {
                  console.log(`Chunk ${chunkCount}:`, parsed.content?.substring(0, 20))
                }
              } else if (parsed.error) {
                throw new Error(parsed.error)
              } else if (parsed.status) {
                // 处理状态更新
                console.log('Stream status:', parsed.status)
              }
            } catch (e) {
              // JSON 解析错误，记录但继续处理
              if (process.env.NODE_ENV === 'development') {
                console.warn('Failed to parse SSE data:', data, e)
              }
            }
          }
        }
      }

      const duration = Date.now() - startTime
      console.log(`Streaming complete: ${chunkCount} chunks in ${duration}ms`)

      // 流式结束，保存完整消息
      if (fullContent) {
        const assistantMessage: Message = {
          id: Date.now().toString(),
          role: 'assistant',
          content: fullContent,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, assistantMessage])

        // 更新学习进度（对话已由后端自动保存）
        try {
          await updateLearningProgress()
        } catch (progressError) {
          console.error('更新学习进度失败:', progressError)
        }
      } else {
        // 没有收到内容，显示错误消息
        throw new Error('未收到响应内容')
      }

    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.log('请求已取消')
        return
      }
      
      const apiError = handleApiError(error)
      const friendlyMessage = getFriendlyErrorMessage(apiError)

      console.error('Streaming error:', apiError)

      // 显示友好的错误提示
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `⚠️ ${friendlyMessage}\n\n请稍后重试，或检查网络连接。`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsStreaming(false)
      setStreamingContent('')
    }
  }

  const handleSend = async () => {
    if (!input.trim() || isStreaming || !userId) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    const messageToSend = input
    setInput('')
    startStreaming(messageToSend)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className={`flex flex-col h-full w-full bg-white ${className}`}>
      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4 min-h-0">
        {isLoadingHistory ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-black"></div>
            <p className="ml-3 text-sm text-gray-500">正在加载学习历史...</p>
          </div>
        ) : (
          <AnimatePresence>
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
          </AnimatePresence>
        )}

        {/* 流式消息（打字机效果） */}
        {isStreaming && streamingContent && (
          <StreamingMessage content={streamingContent} isComplete={false} />
        )}

        {/* 正在思考指示器 */}
        {isStreaming && !streamingContent && (
          <TypingIndicator />
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 输入框 */}
      <div className="border-t border-gray-200 px-6 py-4 bg-white flex-shrink-0">
        <div className="flex items-end gap-3 max-w-5xl mx-auto">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入你的问题... (Shift+Enter 换行)"
            className="flex-1 px-4 py-3 bg-white border-2 border-gray-200 rounded-xl resize-none focus:outline-none focus:border-black transition-all text-sm"
            rows={1}
            disabled={isStreaming}
            style={{ minHeight: '48px', maxHeight: '150px' }}
          />

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleSend}
            disabled={isStreaming || !input.trim()}
            className="px-6 py-3 bg-black text-white rounded-xl hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex-shrink-0 h-12"
          >
            {isStreaming ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </motion.button>
        </div>

        <p className="text-xs text-gray-500 mt-3 text-center max-w-5xl mx-auto">
          按 Enter 发送，Shift+Enter 换行
        </p>
      </div>
    </div>
  )
}
