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

interface StudyChatProps {
  chapterId?: string
  chapterTitle?: string
  studentLevel?: number
  userId?: number
  onStrictnessChange?: (level: number) => void
  className?: string
}

export function StudyChat({
  chapterId = '1',
  chapterTitle = '第一章：线性代数基础',
  studentLevel = 3,
  userId = 1, // 默认用户 ID
  onStrictnessChange,
  className = ''
}: StudyChatProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [currentStrictness, setCurrentStrictness] = useState(studentLevel)
  const [isLoadingHistory, setIsLoadingHistory] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  // 加载历史对话和用户状态
  useEffect(() => {
    const loadHistory = async () => {
      try {
        // 获取历史对话
        const historyResponse = await fetch(
          `http://localhost:8000/api/users/${userId}/history?chapter_number=${chapterId}`
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

          // 更新用户等级
          if (historyData.user_level) {
            setCurrentStrictness(historyData.user_level)
          }
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
        console.error('加载历史失败:', error)
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
  }, [userId, chapterId, chapterTitle])

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingContent])

  // SSE 流式响应
  const startStreaming = async (userMessage: string) => {
    setIsStreaming(true)
    setStreamingContent('')

    try {
      const response = await fetch('http://localhost:8000/api/teaching/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          chapter_id: chapterId,
          student_level: currentStrictness,
          stream: true
        })
      })

      if (!response.ok) throw new Error('Failed to connect to chat API')

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) throw new Error('No reader available')

      let buffer = ''

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
                setStreamingContent(prev => prev + parsed.content)
              }
            } catch (e) {
              // 忽略解析错误
            }
          }
        }
      }

      // 流式结束，保存完整消息
      if (streamingContent) {
        const assistantMessage: Message = {
          id: Date.now().toString(),
          role: 'assistant',
          content: streamingContent,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, assistantMessage])
      }

    } catch (error) {
      console.error('Streaming error:', error)
      // 降级处理：使用模拟数据
      const fallbackMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `抱歉，连接遇到了问题。让我为你讲解一下 **线性代数基础**。\n\n线性代数是研究向量空间和线性变换的数学分支。它在计算机科学、物理学、工程学等领域有广泛应用。\n\n### 核心概念\n\n1. **向量** - 具有大小和方向的量\n2. **矩阵** - 数字的矩形阵列\n3. **线性变换** - 保持向量加法和标量乘法的变换`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, fallbackMessage])
    } finally {
      setIsStreaming(false)
      setStreamingContent('')
    }
  }

  const handleSend = () => {
    if (!input.trim() || isStreaming) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    startStreaming(input)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className={`flex flex-col h-full bg-white ${className}`}>
      {/* 顶部进度条 */}
      <div className="border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-lg font-semibold text-black">{chapterTitle}</h2>
            <p className="text-sm text-gray-500 mt-1">
              当前等级：<span className="font-medium">L{currentStrictness}</span>
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

            {/* 严厉程度浮动菜单 */}
            <div className="absolute right-2 top-1/2 -translate-y-1/2">
              <StrictnessMenu
                currentLevel={currentStrictness}
                onChange={(level) => {
                  setCurrentStrictness(level)
                  onStrictnessChange?.(level)
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
    </div>
  )
}
