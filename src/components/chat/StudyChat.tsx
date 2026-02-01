'use client'

/**
 * StudyChat - 沉浸式学习对话组件
 * 基于 shadcn/ui 风格的现代化设计
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
  subsectionId?: string
  subsectionTitle?: string
  documentId?: number
  teachingStyle?: number
  className?: string
}

export function StudyChat({
  chapterId = '1',
  chapterTitle = '第一章',
  subsectionId,
  subsectionTitle,
  documentId,
  teachingStyle = 3,
  className = ''
}: StudyChatProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')

  // 用户信息状态
  const [userId, setUserId] = useState<number | null>(null)
  const [currentStyle, setCurrentStyle] = useState<number>(teachingStyle)
  const [isLoadingHistory, setIsLoadingHistory] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // 初始化用户信息
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

  // 监听 teachingStyle prop 变化
  useEffect(() => {
    if (teachingStyle && teachingStyle !== currentStyle) {
      setCurrentStyle(teachingStyle)
    }
  }, [teachingStyle])

  // 加载历史对话记录
  useEffect(() => {
    const loadHistory = async () => {
      // 如果没有 userId，直接结束加载
      if (!userId) {
        setIsLoadingHistory(false)
        return
      }

      try {
        const response = await fetch(
          getApiUrl(`/api/users/${userId}/history?chapter_number=${chapterId}`),
          {
            headers: getAuthHeadersSimple()
          }
        )

        if (response.ok) {
          const data = await response.json()
          if (data.conversations && data.conversations.length > 0) {
            // 将历史对话转换为消息格式
            const historyMessages: Message[] = []
            data.conversations.forEach((conv: any) => {
              if (conv.user_message) {
                historyMessages.push({
                  id: `hist-${conv.id}-user`,
                  role: 'user',
                  content: conv.user_message,
                  timestamp: new Date(conv.timestamp)
                })
              }
              if (conv.ai_response) {
                historyMessages.push({
                  id: `hist-${conv.id}-ai`,
                  role: 'assistant',
                  content: conv.ai_response,
                  timestamp: new Date(conv.timestamp)
                })
              }
            })
            setMessages(historyMessages)
          }
        }
      } catch (error) {
        console.error('加载历史对话失败:', error)
      } finally {
        setIsLoadingHistory(false)
      }
    }

    loadHistory()
  }, [userId, chapterId])

  // 自动滚动
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  // 更新学习进度
  const updateLearningProgress = async () => {
    if (!userId) return

    try {
      await fetch(getApiUrl(`/api/users/${userId}/update-chapter-progress`), {
        method: 'POST',
        headers: getAuthHeadersSimple(),
        body: JSON.stringify({
          document_id: documentId || 1,
          chapter_number: parseInt(chapterId, 10),
          chapter_title: chapterTitle,
          time_spent_minutes: 1,
          completion_percentage: null
        })
      })
    } catch (progressError) {
      console.error('更新学习进度失败:', progressError)
    }
  }

  // 开始流式对话
  const startStreaming = async (messageToSend: string) => {
    if (!userId) return

    setIsStreaming(true)
    setStreamingContent('')

    try {
      const response = await fetch(getApiUrl('/api/teaching/chat'), {
        method: 'POST',
        headers: {
          ...getAuthHeadersSimple(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: messageToSend,
          chapter_id: chapterId,
          student_level: currentStyle,
          stream: true,
          user_id: userId,
          document_id: documentId,
          subsection_id: subsectionId,
          subsection_title: subsectionTitle
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('无法读取响应流')
      }

      let fullContent = ''

      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim()

            if (data === '[DONE]') {
              // 流式完成
              setStreamingContent('')

              const assistantMessage: Message = {
                id: Date.now().toString(),
                role: 'assistant',
                content: fullContent,
                timestamp: new Date()
              }

              setMessages(prev => [...prev, assistantMessage])
              fullContent = ''
              break
            }

            try {
              const parsed = JSON.parse(data)

              if (parsed.content) {
                fullContent += parsed.content
                setStreamingContent(fullContent)
              }
            } catch (parseError) {
              // 忽略解析错误
            }
          }
        }

        scrollToBottom()
      }

      // 更新进度
      try {
        await updateLearningProgress()
      } catch (progressError) {
        console.error('更新学习进度失败:', progressError)
      }

    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.log('请求已取消')
        return
      }

      const apiError = handleApiError(error)
      const friendlyMessage = getFriendlyErrorMessage(apiError)

      console.error('Streaming error:', apiError)

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
    <div className={`flex flex-col h-full bg-gray-50 ${className}`}>
      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto">
        {isLoadingHistory ? (
          <div className="flex items-center justify-center h-full min-h-[400px]">
            <div className="flex flex-col items-center gap-4">
              <div className="animate-spin rounded-full h-10 w-10 border-3 border-gray-300 border-t-indigo-600"></div>
              <p className="text-sm text-gray-600 font-medium">加载学习历史中...</p>
            </div>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex items-center justify-center h-full min-h-[400px] px-4">
            <div className="text-center max-w-md">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-100 rounded-full mb-4">
                <span className="text-3xl">💬</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                开始学习吧！
              </h3>
              <p className="text-sm text-gray-600">
                提问任何问题，AI 导师会为你解答
              </p>
            </div>
          </div>
        ) : (
          <div className="py-2">
            <AnimatePresence mode="popLayout">
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}
            </AnimatePresence>
          </div>
        )}

        {/* 流式消息 */}
        {isStreaming && streamingContent && (
          <StreamingMessage content={streamingContent} isComplete={false} />
        )}

        {/* 正在思考指示器 */}
        {isStreaming && !streamingContent && (
          <div className="px-4 py-6">
            <TypingIndicator />
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 输入框 */}
      <div className="border-t border-gray-200 bg-white px-4 py-4 flex-shrink-0">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-end gap-3">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="输入你的问题... (Shift+Enter 换行)"
                className="w-full px-4 py-3 pr-12 bg-gray-50 border-2 border-gray-200 rounded-xl resize-none focus:outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/20 transition-all text-sm placeholder:text-gray-400"
                rows={1}
                disabled={isStreaming}
                style={{ minHeight: '52px', maxHeight: '160px' }}
              />
              <div className="absolute right-3 bottom-3 text-xs text-gray-400">
                {input.length > 0 && `${input.length} 字`}
              </div>
            </div>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleSend}
              disabled={isStreaming || !input.trim()}
              className="px-5 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-xl hover:from-indigo-600 hover:to-purple-700 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed transition-all duration-200 shadow-sm hover:shadow-md flex-shrink-0 h-[52px] flex items-center justify-center gap-2 font-medium text-sm"
            >
              {isStreaming ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  <Send className="w-5 h-5" />
                  <span className="hidden sm:inline">发送</span>
                </>
              )}
            </motion.button>
          </div>

          <p className="text-xs text-gray-500 mt-2 text-center">
            按 Enter 发送，Shift+Enter 换行
          </p>
        </div>
      </div>
    </div>
  )
}
