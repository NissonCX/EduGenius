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
  const [chartData, setChartData] = useState<DataPoint[]>([])
  const [timeRange, setTimeRange] = useState<'week' | 'month' | 'all'>('week')

  // 生成示例数据（定义在 useMemo 之前）
  const generateSampleData = () => {
    const sampleData: DataPoint[] = []
    const today = new Date()

    for (let i = 29; i >= 0; i--) {
      const date = new Date(today)
      date.setDate(date.getDate() - i)

      // 模拟学习进度增长
      const baseProgress = 20 + (30 - i) * 2.5 + Math.random() * 10
      const baseTime = 30 + Math.random() * 60

      sampleData.push({
        date: date.toISOString().split('T')[0],
        progress: Math.min(100, Math.round(baseProgress)),
        timeSpent: Math.round(baseTime),
        avgScore: Math.round(60 + Math.random() * 35)
      })
    }

    return sampleData
  }

  // 生成示例数据（使用 useMemo 避免重复生成）
  const sampleData = useMemo(() => generateSampleData(), [])

  // 根据时间范围过滤数据
  const filteredData = useMemo(() => {
    const useData = data.length > 0 ? data : sampleData

    const now = new Date()
    let days = 7

    if (timeRange === 'week') days = 7
    else if (timeRange === 'month') days = 30
    else days = 90

    const cutoffDate = new Date(now)
    cutoffDate.setDate(cutoffDate.getDate() - days)

    return useData.filter(d => new Date(d.date) >= cutoffDate)
  }, [data, timeRange, sampleData])

  // 初始化 chartData
  useEffect(() => {
    setChartData(filteredData)
  }, [filteredData])

  // 格式化日期显示
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return `${date.getMonth() + 1}/${date.getDate()}`
  }

  // 计算统计信息
  const stats = {
    avgProgress: chartData.length > 0
      ? Math.round(chartData.reduce((sum, d) => sum + d.progress, 0) / chartData.length)
      : 0,
    totalTime: chartData.reduce((sum, d) => sum + d.timeSpent, 0),
    totalDays: chartData.length,
    progress: chartData.length > 0
      ? Math.round(chartData[chartData.length - 1].progress - chartData[0].progress)
      : 0
  }

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
              formatter={(value: any, name: string) => {
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
