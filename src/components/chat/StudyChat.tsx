'use client'

/**
 * StudyChat - 沉浸式学习对话组件
 * 支持 SSE 流式传输、打字机效果、Markdown 渲染
 * 支持会话恢复和历史记录加载
 */

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Loader2, User, Bot } from 'lucide-react'
import { Message } from '@/types/chat'
import { ChatMessage } from './ChatMessage'
import { TypingIndicator } from './TypingIndicator'
import { StrictnessMenu } from './StrictnessMenu'
import { useAuth } from '@/hooks/useAuth'
import { safeFetch, handleApiError, getFriendlyErrorMessage } from '@/lib/errors'

interface StudyChatProps {
  chapterId?: string
  chapterTitle?: string
  studentLevel?: number
  onStrictnessChange?: (level: number) => void
  className?: string
}

export function StudyChat({
  chapterId = '1',
  chapterTitle = '第一章：线性代数基础',
  studentLevel,
  onStrictnessChange,
  className = ''
}: StudyChatProps) {
  // 使用 useAuth hook 获取真实用户信息
  const { user, token, isAuthenticated, getAuthHeaders } = useAuth()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  // 导师风格（可临时调整，不保存到数据库）
  // 初始化为用户偏好的风格，如果没有则使用默认值3
  const [currentStyle, setCurrentStyle] = useState<number>(user?.teachingStyle || 3)
  const [isLoadingHistory, setIsLoadingHistory] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // 当用户数据加载完成后，更新导师风格
  useEffect(() => {
    if (user?.teachingStyle && user.teachingStyle !== currentStyle) {
      setCurrentStyle(user.teachingStyle)
    }
  }, [user?.teachingStyle, currentStyle])

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  // 保存对话到数据库
  const saveConversationToDB = async (userMsg: string, aiMsg: string) => {
    if (!user.id) return

    try {
      // 更新学习进度（增加1分钟学习时间）
      await fetch(`http://localhost:8000/api/users/${user.id}/update-chapter-progress`, {
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
      await fetch(`http://localhost:8000/api/users/${user.id}/save-conversation`, {
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
      await fetch(`http://localhost:8000/api/users/${user.id}/save-conversation`, {
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
    const loadHistory = async () => {
      // 不要在这里使用 early return，确保 Hooks 顺序一致
      if (!user.id) {
        setIsLoadingHistory(false)
        return
      }

      try {
        // 获取历史对话，使用真实用户 ID（使用 safeFetch）
        const historyResponse = await safeFetch(
          `http://localhost:8000/api/users/${user.id}/history?chapter_number=${chapterId}`,
          {
            headers: getAuthHeaders()
          }
        )

        if (historyResponse.ok) {
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

          setMessages(historyMessages)

        } else {
          // API 失败，显示默认欢迎消息
          setMessages([{
            id: 'welcome',
            role: 'assistant',
            content: `👋 欢迎来到 **${chapterTitle}**！\n\n我是你的 AI 导师。今天我们将一起探索这个章节的核心概念。\n\n让我们开始吧！请告诉我你想了解的内容，或者我可以为你讲解重点知识。`,
            timestamp: new Date()
          }])
        }
      } catch (error) {
        const apiError = handleApiError(error)
        console.error('加载历史失败:', apiError)
        // 显示默认欢迎消息
        setMessages([{
          id: 'welcome',
          role: 'assistant',
          content: `👋 欢迎来到 **${chapterTitle}**！\n\n我是你的 AI 导师。今天我们将一起探索这个章节的核心概念。\n\n让我们开始吧！请告诉我你想了解的内容，或者我可以为你讲解重点知识。`,
          timestamp: new Date()
        }])
      } finally {
        setIsLoadingHistory(false)
      }
    }

    loadHistory()
  }, [user.id, chapterId, chapterTitle])

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingContent])

  // SSE 流式响应
  const startStreaming = async (userMessage: string) => {
    setIsStreaming(true)
    setStreamingContent('')

    try {
      const response = await safeFetch('http://localhost:8000/api/teaching/chat', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          message: userMessage,
          chapter_id: chapterId,
          student_level: currentStyle,
          stream: true,
          user_id: user.id // 传递真实用户 ID
        })
      })

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) throw new Error('No reader available')

      let buffer = ''
      let fullContent = '' // 本地累积完整内容

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') continue

            try {
              const parsed = JSON.parse(data)
              if (parsed.content) {
                fullContent += parsed.content
                setStreamingContent(fullContent)
              }
            } catch (e) {
              // 忽略解析错误
            }
          }
        }
      }

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
          // 不影响用户体验，静默失败
        }
      }

    } catch (error) {
      const apiError = handleApiError(error)
      const friendlyMessage = getFriendlyErrorMessage(apiError)

      console.error('Streaming error:', apiError)

      // 降级处理：显示友好的错误提示
      const fallbackMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `⚠️ ${friendlyMessage}\n\n请稍后重试，或检查网络连接。`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, fallbackMessage])
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
      {/* 如果用户未登录，显示提示 */}
      {!isAuthenticated || !user.id ? (
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
          {/* 顶部进度条 */}
          <div className="border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-lg font-semibold text-black">{chapterTitle}</h2>
            <p className="text-sm text-gray-500 mt-1">
              当前风格：<span className="font-medium">L{currentStyle}</span>
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500">学习进度</p>
            <p className="text-2xl font-semibold text-emerald-600 mt-1">65%</p>
          </div>
        </div>

        {/* 流光进度条 */}
        <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-emerald-400 to-emerald-600 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: '65%' }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
          />
        </div>
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
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
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex gap-3"
          >
            <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
              <Bot className="w-5 h-5 text-gray-600" />
            </div>
            <div className="flex-1 max-w-3xl">
              <div className="bg-gray-50 rounded-2xl rounded-tl-sm p-4 border border-gray-100">
                <div className="prose prose-sm max-w-none">
                  {/* 这里会使用打字机效果组件渲染 */}
                  <span>{streamingContent}</span>
                  <span className="inline-block w-0.5 h-4 bg-gray-800 animate-pulse ml-0.5" />
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-1.5 ml-2">
                正在输入...
              </p>
            </div>
          </motion.div>
        )}

        {/* 正在思考指示器 */}
        {isStreaming && !streamingContent && (
          <TypingIndicator />
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 输入框 */}
      <div className="border-t border-gray-200 px-6 py-4 bg-white relative">
        <div className="flex items-end gap-3 max-w-4xl mx-auto">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入你的问题... (Shift+Enter 换行)"
              className="w-full px-4 py-3 pr-14 bg-white border border-gray-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent transition-all text-sm"
              rows={1}
              disabled={isStreaming}
              style={{ minHeight: '48px', maxHeight: '150px' }}
            />

            {/* 导师风格浮动菜单 */}
            <div className="absolute right-2 top-1/2 -translate-y-1/2">
              <StrictnessMenu
                currentLevel={currentStyle}
                onChange={(level) => {
                  setCurrentStyle(level)
                }}
              />
            </div>
          </div>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleSend}
            disabled={isStreaming || !input.trim()}
            className="px-4 py-3 bg-black text-white rounded-xl hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex-shrink-0"
          >
            {isStreaming ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </motion.button>
        </div>

        <p className="text-xs text-gray-500 mt-2 text-center">
          按 Enter 发送，Shift+Enter 换行 · AI 导师会根据你的等级调整教学风格
        </p>
      </div>
        </>
      )}
    </div>
  )
}
