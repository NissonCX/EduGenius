'use client'

/**
 * StudyCalendar - 学习日历热力图组件
 * 显示过去一段时间的学习活跃度
 */

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'

interface StudyDay {
  date: string
  count: number // 学习次数或分钟数
}

interface StudyCalendarProps {
  studyDays?: StudyDay[]
  weeks?: number // 显示多少周，默认12周
}

export function StudyCalendar({ studyDays = [], weeks = 12 }: StudyCalendarProps) {
  const [calendarData, setCalendarData] = useState<StudyDay[]>([])

  useEffect(() => {
    // 生成日历数据
    const generateCalendarData = () => {
      const data: StudyDay[] = []
      const today = new Date()

      for (let i = 0; i < weeks * 7; i++) {
        const date = new Date(today)
        date.setDate(date.getDate() - i)

        const dateStr = date.toISOString().split('T')[0]
        const existing = studyDays.find(d => d.date === dateStr)

        data.push({
          date: dateStr,
          count: existing?.count || 0
        })
      }

      return data.reverse()
    }

    setCalendarData(generateCalendarData())
  }, [studyDays, weeks])

  // 按周分组
  const weeksData: StudyDay[][] = []
  for (let i = 0; i < calendarData.length; i += 7) {
    weeksData.push(calendarData.slice(i, i + 7))
  }

  // 获取颜色级别
  const getColorLevel = (count: number) => {
    if (count === 0) return 'bg-gray-100'
    if (count <= 30) return 'bg-gray-300'
    if (count <= 60) return 'bg-gray-500'
    if (count <= 120) return 'bg-gray-700'
    return 'bg-black'
  }

  // 计算总学习时间
  const totalStudyTime = studyDays.reduce((sum, day) => sum + day.count, 0)
  const avgStudyTime = studyDays.length > 0 ? Math.round(totalStudyTime / studyDays.length) : 0
  const maxDay = studyDays.reduce((max, day) => day.count > max ? day.count : max, 0)

  // 获取星期几标签
  const weekDays = ['日', '一', '二', '三', '四', '五', '六']

  return (
    <div className="w-full">
      {/* 标题和统计 */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-black">学习日历</h3>
          <p className="text-xs text-gray-500 mt-1">
            过去 {weeks} 周的学习活跃度
          </p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-light text-black">{totalStudyTime}</p>
          <p className="text-xs text-gray-500 uppercase tracking-wide">总分钟数</p>
        </div>
      </div>

      {/* 日历网格 */}
      <div className="bg-white border border-gray-200 rounded-xl p-4">
        {/* 星期标签 */}
        <div className="grid grid-cols-8 gap-1 mb-2">
          <div></div>
          {weekDays.map((day, index) => (
            <div key={index} className="text-xs text-gray-500 text-center">
              {day}
            </div>
          ))}
        </div>

        {/* 日历格子 */}
        <div className="space-y-1">
          {weeksData.map((week, weekIndex) => (
            <div key={weekIndex} className="grid grid-cols-8 gap-1">
              {/* 周数标签 */}
              <div className="text-xs text-gray-400 flex items-center">
                {weekIndex + 1}
              </div>

              {/* 一周7天 */}
              {week.map((day, dayIndex) => (
                <motion.div
                  key={`${weekIndex}-${dayIndex}`}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.2, delay: (weekIndex * 7 + dayIndex) * 0.01 }}
                  className="aspect-square"
                >
                  <div
                    className={`
                      w-full h-full rounded-sm cursor-pointer
                      transition-all duration-200 hover:ring-1 hover:ring-gray-400
                      ${getColorLevel(day.count)}
                    `}
                    title={`${day.date}: ${day.count} 分钟`}
                  />
                </motion.div>
              ))}
            </div>
          ))}
        </div>

        {/* 图例 */}
        <div className="flex items-center justify-end gap-2 mt-4 text-xs text-gray-500">
          <span>少</span>
          <div className="flex gap-1">
            <div className="w-3 h-3 bg-gray-100 rounded-sm"></div>
            <div className="w-3 h-3 bg-gray-300 rounded-sm"></div>
            <div className="w-3 h-3 bg-gray-500 rounded-sm"></div>
            <div className="w-3 h-3 bg-gray-700 rounded-sm"></div>
            <div className="w-3 h-3 bg-black rounded-sm"></div>
          </div>
          <span>多</span>
        </div>
      </div>

      {/* 统计摘要 */}
      <div className="grid grid-cols-3 gap-3 mt-4">
        <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
          <p className="text-xs text-gray-600">平均每天</p>
          <p className="text-lg font-semibold text-black mt-1">{avgStudyTime}分钟</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
          <p className="text-xs text-gray-600">最长一天</p>
          <p className="text-lg font-semibold text-black mt-1">{maxDay}分钟</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
          <p className="text-xs text-gray-600">活跃天数</p>
          <p className="text-lg font-semibold text-black mt-1">{studyDays.filter(d => d.count > 0).length}天</p>
        </div>
      </div>
    </div>
  )
}
