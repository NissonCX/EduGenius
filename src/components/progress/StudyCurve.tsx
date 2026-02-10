'use client'

/**
 * StudyCurve - 学习曲线图表组件
 * 显示学习进度和能力成长趋势
 */

import { useState, useEffect, useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts'

interface DataPoint {
  date: string
  progress: number // 完成度百分比
  timeSpent: number // 学习时长（分钟）
  avgScore?: number // 平均分数
}

interface StudyCurveProps {
  data?: DataPoint[]
}

export function StudyCurve({ data = [] }: StudyCurveProps) {
  const [timeRange, setTimeRange] = useState<'week' | 'month' | 'all'>('month')

  // 根据时间范围过滤数据
  const chartData = useMemo(() => {
    if (data.length === 0) {
      return []
    }

    const now = new Date()
    let days = 7

    if (timeRange === 'week') days = 7
    else if (timeRange === 'month') days = 30
    else days = 90

    const cutoffDate = new Date(now)
    cutoffDate.setDate(cutoffDate.getDate() - days)

    return data.filter(d => new Date(d.date) >= cutoffDate)
  }, [data, timeRange])

  // 格式化日期显示
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return `${date.getMonth() + 1}/${date.getDate()}`
  }

  // 计算统计信息
  const stats = useMemo(() => {
    if (chartData.length === 0) {
      return {
        avgProgress: 0,
        totalTime: 0,
        totalDays: 0,
        progress: 0
      }
    }

    const avgProgress = Math.round(chartData.reduce((sum, d) => sum + d.progress, 0) / chartData.length)
    const totalTime = chartData.reduce((sum, d) => sum + d.timeSpent, 0)
    const totalDays = chartData.length

    // 计算进度增长：最后一个有学习活动的日期的进度 - 初始进度
    // 找到最后一个有学习时长的数据点作为"当前"进度
    const lastActiveDay = [...chartData].reverse().find(d => d.timeSpent > 0)
    const firstActiveDay = [...chartData].find(d => d.timeSpent > 0)

    let progressGrowth = 0
    if (lastActiveDay && firstActiveDay && lastActiveDay !== firstActiveDay) {
      progressGrowth = Math.round(lastActiveDay.progress - firstActiveDay.progress)
    } else if (lastActiveDay) {
      // 只有一天有学习活动
      progressGrowth = Math.round(lastActiveDay.progress)
    }

    return {
      avgProgress,
      totalTime,
      totalDays,
      progress: progressGrowth
    }
  }, [chartData])

  return (
    <div className="w-full">
      {/* 标题和统计 */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-black">学习曲线</h3>
          <p className="text-xs text-gray-500 mt-1">
            进度和学习时长趋势
          </p>
        </div>

        {/* 时间范围选择器 */}
        <div className="flex gap-1">
          {(['week', 'month', 'all'] as const).map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`
                px-3 py-1 text-xs rounded-lg transition-all
                ${timeRange === range
                  ? 'bg-black text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }
              `}
            >
              {range === 'week' ? '7天' : range === 'month' ? '30天' : '全部'}
            </button>
          ))}
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-4 gap-3 mb-4">
        <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
          <p className="text-xs text-gray-600">平均完成度</p>
          <p className="text-lg font-semibold text-black mt-1">{stats.avgProgress}%</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
          <p className="text-xs text-gray-600">总学习时长</p>
          <p className="text-lg font-semibold text-black mt-1">{Math.round(stats.totalTime / 60)}h</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
          <p className="text-xs text-gray-600">学习天数</p>
          <p className="text-lg font-semibold text-black mt-1">{stats.totalDays}天</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
          <p className="text-xs text-gray-600">进度增长</p>
          <p className={`text-lg font-semibold mt-1 ${stats.progress >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {stats.progress > 0 ? '+' : ''}{stats.progress}%
          </p>
        </div>
      </div>

      {/* 图表 */}
      <div className="bg-white border border-gray-200 rounded-xl p-4">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" strokeWidth={0.5} />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              tick={{ fill: '#6B7280', fontSize: 11 }}
              tickLine={false}
            />
            <YAxis
              yAxisId="left"
              tick={{ fill: '#6B7280', fontSize: 11 }}
              tickLine={false}
              tickFormatter={(value) => `${value}%`}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fill: '#6B7280', fontSize: 11 }}
              tickLine={false}
              tickFormatter={(value) => `${value}m`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #E5E7EB',
                borderRadius: '8px',
                fontSize: '12px'
              }}
              labelFormatter={(label) => `日期: ${label}`}
              formatter={(value: any, name?: string) => {
                if (name === '完成度') return [`${value}%`, name]
                if (name === '学习时长') return [`${value}分钟`, name]
                return [value, name]
              }}
            />
            <Legend />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="progress"
              stroke="#111827"
              strokeWidth={2}
              dot={{ r: 3 }}
              name="完成度"
              activeDot={{ r: 5 }}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="timeSpent"
              stroke="#9CA3AF"
              strokeWidth={2}
              dot={{ r: 3 }}
              name="学习时长"
              activeDot={{ r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
