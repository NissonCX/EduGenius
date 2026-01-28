'use client'

/**
 * /study - 沉浸式学习对话页面
 * 整合聊天界面和侧边栏
 */

import { useState, useEffect } from 'react'
import { StudyChat } from '@/components/chat/StudyChat'
import { StudySidebar } from '@/components/chat/StudySidebar'
import { useAuth } from '@/contexts/AuthContext'

export default function StudyPage() {
  const { user } = useAuth()
  const [completedTopics, setCompletedTopics] = useState<string[]>([
    '向量的定义',
    '向量的表示方法'
  ])

  // 使用用户的导师风格，如果没有则使用默认值3
  const [teachingStyle, setTeachingStyle] = useState(user?.teachingStyle || 3)

  // 当用户的 teachingStyle 更新时同步
  useEffect(() => {
    if (user?.teachingStyle) {
      setTeachingStyle(user.teachingStyle)
    }
  }, [user?.teachingStyle])

  const keyPoints = [
    '向量的定义',
    '向量的表示方法',
    '向量的运算规则',
    '向量的应用场景',
    '向量的几何意义',
    '特殊向量（零向量、单位向量）',
    '向量空间的定义',
    '线性相关与线性无关'
  ]

  const handleStyleChange = (style: number) => {
    setTeachingStyle(style)
    console.log('Teaching style changed to:', style)
  }

  return (
    <div className="flex h-screen bg-white">
      {/* 主聊天区域 */}
      <div className="flex-1 flex flex-col">
        <StudyChat
          chapterId="1"
          chapterTitle="第一章：线性代数基础"
          studentLevel={teachingStyle}
          onStrictnessChange={handleStyleChange}
        />
      </div>

      {/* 右侧边栏 */}
      <StudySidebar
        teachingStyle={teachingStyle}
        chapterTitle="第一章：线性代数基础"
        keyPoints={keyPoints}
        completedTopics={completedTopics}
      />
    </div>
  )
}
