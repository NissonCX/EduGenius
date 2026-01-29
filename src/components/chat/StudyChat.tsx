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
import { useAuth } from '@/contexts/AuthContext'
import { safeFetch, handleApiError, getFriendlyErrorMessage } from '@/lib/errors'
import { getApiUrl } from '@/lib/config'

interface StudyChatProps {
  chapterId?: string
  chapterTitle?: string
  className?: string
}

export function StudyChat({
  chapterId = '1',
  chapterTitle = '第一章：线性代数基础',
  className = ''
}: StudyChatProps) {
  // 使用 useAuth hook 获取真实用户信息
  const { user, isAuthenticated, getAuthHeaders } = useAuth()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  // 导师风格（可临时调整，不保存到数据库）
  // 直接从 user 对象获取，如果用户未登录则使用默认值3
  const userStyle = user?.teachingStyle || 3
  const [currentStyle, setCurrentStyle] = useState<number>(userStyle)
  const [isLoadingHistory, setIsLoadingHistory] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // 当用户的 teachingStyle 改变时，同步更新 currentStyle
  useEffect(() => {
    if (user?.teachingStyle) {
      setCurrentStyle(user.teachingStyle)
    }
  }, [user?.teachingStyle])

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  // 保存对话到数据库
  const saveConversationToDB = async (userMsg: string, aiMsg: string) => {
    if (!user.id) return

    try {
      // 更新学习进度（增加1分钟学习时间）
      await fetch(getApiUrl(`/api/users/${user.id}/update-chapter-progress`), {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          document_id: 1, // TODO: 从上下文获取真实 document_id
          chapter_number: parseInt(chapterId, 10),
          chapter_title: chapterTitle,
          time_spent_minutes: 1,
          completion_percentage: null // 让后端自动计算
        })
      })

      // 保存用户消息
      await fetch(getApiUrl(`/api/users/${user.id}/save-conversation`), {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          role: 'user',
          content: userMsg,
          chapter_number: parseInt(chapterId, 10),
          document_id: 1 // TODO: 从上下文获取真实 document_id
        })
      })

      // 保存 AI 回复
      await fetch(getApiUrl(`/api/users/${user.id}/save-conversation`), {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          role: 'assistant',
          content: aiMsg,
          chapter_number: parseInt(chapterId, 10),
          document_id: 1
        })
      })
    } catch (error) {
      console.error('保存对话失败:', error)
      throw error
    }
  }

  // 加载历史对话和用户状态
  useEffect(() => {
    let isMounted = true // 防止组件卸载后更新状态
    const abortController = new AbortController() // 取消请求

    const loadHistory = async () => {
      // 不要在这里使用 early return，确保 Hooks 顺序一致
      if (!user.id) {
        setIsLoadingHistory(false)
        return
      }

      try {
        // 获取历史对话，使用真实用户 ID（使用 safeFetch）
        const historyResponse = await safeFetch(
          getApiUrl(`/api/users/${user.id}/history?chapter_number=${chapterId}`),
          {
            headers: getAuthHeaders(),
            signal: abortController.signal
          }
        )

        if (historyResponse.ok && isMounted) {
          const historyData = await historyResponse.json()

          // 转换历史对话为 Message 格式
          const historyMessages: Message[] = historyData.conversations.map((conv: any) => ({
            id: conv.id.toString(),
            role: conv.role as 'user' | 'assistant',
            content: conv.content,
            timestamp: new Date(conv.created_at)
          }))

          // 如果没有历史记录，显示欢迎消息
          if (historyMessages.length === 0) {
            historyMessages.push({
              id: 'welcome',
              role: 'assistant',
              content: `👋 欢迎来到 **${chapterTitle}**！\n\n我是你的 AI 导师。今天我们将一起探索这个章节的核心概念。\n\n让我们开始吧！请告诉我你想了解的内容，或者我可以为你讲解重点知识。`,
              timestamp: new Date()
            })
          }

          if (isMounted) {
            setMessages(historyMessages)
          }

        } else if (isMounted) {
          // API 失败，显示默认欢迎消息
          setMessages([{
            id: 'welcome',
            role: 'assistant',
            content: `👋 欢迎来到 **${chapterTitle}**！\n\n我是你的 AI 导师。今天我们将一起探索这个章节的核心概念。\n\n让我们开始吧！请告诉我你想了解的内容，或者我可以为你讲解重点知识。`,
            timestamp: new Date()
          }])
        }
      } catch (error: any) {
        if (error.name === 'AbortError') {
          console.log('请求已取消')
          return
        }
        
        const apiError = handleApiError(error)
        console.error('加载历史失败:', apiError)
        
        // 显示默认欢迎消息
        if (isMounted) {
          setMessages([{
            id: 'welcome',
            role: 'assistant',
            content: `👋 欢迎来到 **${chapterTitle}**！\n\n我是你的 AI 导师。今天我们将一起探索这个章节的核心概念。\n\n让我们开始吧！请告诉我你想了解的内容，或者我可以为你讲解重点知识。`,
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
  }, [user.id, chapterId, chapterTitle, getAuthHeaders])

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingContent])

  // SSE 流式响应（优化版）
  const startStreaming = async (userMessage: string) => {
    setIsStreaming(true)
    setStreamingContent('')
    
    const abortController = new AbortController()

    try {
      const response = await safeFetch(getApiUrl('/api/teaching/chat'), {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          message: userMessage,
          chapter_id: chapterId,
          student_level: currentStyle,
          stream: true,
          user_id: user.id
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

        // 保存对话到数据库
        try {
          await saveConversationToDB(userMessage, fullContent)
        } catch (saveError) {
          console.error('保存对话失败:', saveError)
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
    if (!input.trim() || isStreaming || !user.id) return

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
    <div className={`flex flex-col h-full bg-white ${className}`}>
      {/* 🔧 FIX: 只在明确未认证时显示登录提示，不在加载中时显示 */}
      {isAuthenticated === false || !user.id ? (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <p className="text-gray-500 mb-4">请先登录以开始学习</p>
            <a
              href="/login"
              className="px-6 py-2 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors"
            >
              前往登录
            </a>
          </div>
        </div>
      ) : (
        <>
          {/* 消息列表 */}
          <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
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
          <div className="border-t border-gray-200 px-6 py-4 bg-white">
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
        </>
      )}
    </div>
  )
}
