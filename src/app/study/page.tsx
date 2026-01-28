'use client'

/**
 * /study - 沉浸式学习对话页面
 * 整合聊天界面和侧边栏
 */

import { useState } from 'react'
import { StudyChat } from '@/components/chat/StudyChat'
import { StudySidebar } from '@/components/chat/StudySidebar'

export default function StudyPage() {
  const [studentLevel, setStudentLevel] = useState(3)
  const [completedTopics, setCompletedTopics] = useState<string[]>([
    '向量的定义',
    '向量的表示方法'
  ])

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

  const handleStrictnessChange = (level: number) => {
    setStudentLevel(level)
    // 这里可以添加 API 调用来更新用户等级
    console.log('Strictness changed to:', level)
  }

  return (
    <div className="flex h-screen bg-white">
      {/* 主聊天区域 */}
      <div className="flex-1 flex flex-col">
        <StudyChat
          chapterId="1"
          chapterTitle="第一章：线性代数基础"
          studentLevel={studentLevel}
          onStrictnessChange={handleStrictnessChange}
        />
      </div>

      {/* 右侧边栏 */}
      <StudySidebar
        studentLevel={studentLevel}
        chapterTitle="第一章：线性代数基础"
        keyPoints={keyPoints}
        completedTopics={completedTopics}
      />
    </div>
  )
}
