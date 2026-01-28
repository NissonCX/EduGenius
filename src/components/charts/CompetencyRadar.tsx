'use client'

/**
 * CompetencyRadar - 学习能力雷达图组件
 *
 * 展示学生的六维能力评估：
 * - 理解力 (Comprehension)
 * - 逻辑 (Logic)
 * - 术语 (Terminology)
 * - 记忆 (Memory)
 * - 应用 (Application)
 * - 稳定性 (Stability)
 */

import { useState, useEffect } from 'react'
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer
} from 'recharts'

// 能力维度定义
const COMPETENCY_DIMENSIONS = [
  { key: 'comprehension', label: '理解力' },
  { key: 'logic', label: '逻辑' },
  { key: 'terminology', label: '术语' },
  { key: 'memory', label: '记忆' },
  { key: 'application', label: '应用' },
  { key: 'stability', label: '稳定性' }
]

interface CompetencyData {
  dimension: string
  value: number
  fullMark: number
}

interface CompetencyRadarProps {
  data?: {
    comprehension?: number
    logic?: number
    terminology?: number
    memory?: number
    application?: number
    stability?: number
  }
  className?: string
}

// 默认数据（用于演示）
const DEFAULT_DATA: CompetencyData[] = [
  { dimension: '理解力', value: 75, fullMark: 100 },
  { dimension: '逻辑', value: 68, fullMark: 100 },
  { dimension: '术语', value: 82, fullMark: 100 },
  { dimension: '记忆', value: 90, fullMark: 100 },
  { dimension: '应用', value: 60, fullMark: 100 },
  { dimension: '稳定性', value: 72, fullMark: 100 }
]

export function CompetencyRadar({
  data: propData,
  className
}: CompetencyRadarProps) {
  const [chartData, setChartData] = useState<CompetencyData[]>(DEFAULT_DATA)
  const [isLoading, setIsLoading] = useState(false)

  // 从 API 获取数据
  useEffect(() => {
    const fetchCompetencyData = async () => {
      setIsLoading(true)
      try {
        // 临时：使用传入的数据或默认数据
        if (propData) {
          const formatted = COMPETENCY_DIMENSIONS.map(dim => ({
            dimension: dim.label,
            value: propData[dim.key as keyof typeof propData] || 70,
            fullMark: 100
          }))
          setChartData(formatted)
        }
      } catch (error) {
        console.error('Failed to fetch competency data:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchCompetencyData()
  }, [propData])

  // 计算平均分
  const averageScore = Math.round(
    chartData.reduce((sum, item) => sum + item.value, 0) / chartData.length
  )

  // 现代配色方案（使用紫色渐变）
  const radarColor = 'rgba(99, 102, 241, 0.25)'
  const strokeColor = 'rgba(99, 102, 241, 1)'

  return (
    <div className={className}>
      {/* 标题区域 */}
      <div className="mb-6">
        <div className="flex items-end justify-between">
          <div>
            <h3 className="text-lg font-semibold text-black">学习能力分析</h3>
            <p className="text-xs text-gray-500 mt-1">
              基于答题记录评估
            </p>
          </div>
          <div className="text-right">
            <p className="text-3xl font-light text-black">{averageScore}</p>
            <p className="text-xs text-gray-500 uppercase tracking-wide">综合评分</p>
          </div>
        </div>
      </div>

      {/* 雷达图 */}
      {isLoading ? (
        <div className="w-full h-64 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={280}>
          <RadarChart data={chartData}>
            <PolarGrid
              stroke="#E5E7EB"
              strokeWidth={0.5}
            />
            <PolarAngleAxis
              dataKey="dimension"
              tick={{ fill: '#6B7280', fontSize: 11 }}
              className="text-xs"
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 100]}
              tick={false}
              stroke="#E5E7EB"
              strokeWidth={0.5}
            />
            <Radar
              name="能力值"
              dataKey="value"
              stroke={strokeColor}
              fill={radarColor}
              strokeWidth={1.5}
              dot={{ r: 2, fill: strokeColor }}
              animationBegin={0}
              animationDuration={800}
            />
          </RadarChart>
        </ResponsiveContainer>
      )}

      {/* 简化的维度列表 */}
      <div className="mt-6 space-y-2">
        {chartData.map((item, index) => (
          <div
            key={index}
            className="flex items-center gap-3"
          >
            <div
              className="w-16 text-xs text-gray-600 text-right"
              style={{ flexShrink: 0 }}
            >
              {item.dimension}
            </div>
            <div
              className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden"
              style={{ flexShrink: 1 }}
            >
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${item.value}%`,
                  backgroundColor: item.value >= 80 ? '#10B981' : item.value >= 60 ? strokeColor : '#9CA3AF'
                }}
              />
            </div>
            <div
              className="w-8 text-xs font-medium text-right"
              style={{ flexShrink: 0 }}
            >
              {item.value}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
