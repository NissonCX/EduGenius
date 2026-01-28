'use client'

/**
 * KnowledgeConstellation - 知识星座图组件
 * 优化版：更精致的视觉效果、流畅动画、优雅的交互
 */

import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'

interface KnowledgeNode {
  id: string
  label: string
  status: 'completed' | 'in-progress' | 'locked'
  category: string
  value?: number
}

interface KnowledgeLink {
  source: string
  target: string
  strength: number
}

interface KnowledgeConstellationProps {
  nodes?: KnowledgeNode[]
  links?: KnowledgeLink[]
  onNodeClick?: (node: KnowledgeNode) => void
  className?: string
  height?: number
}

// 默认演示数据
const DEFAULT_NODES: KnowledgeNode[] = [
  { id: 'root', label: '核心概念', status: 'completed', category: 'core', value: 3 },
  { id: 'basic1', label: '基础理论', status: 'completed', category: 'basic', value: 2 },
  { id: 'basic2', label: '定义与术语', status: 'completed', category: 'basic', value: 2 },
  { id: 'inter1', label: '应用场景', status: 'in-progress', category: 'intermediate', value: 2 },
  { id: 'inter2', label: '实际案例', status: 'in-progress', category: 'intermediate', value: 2 },
  { id: 'adv1', label: '高级应用', status: 'locked', category: 'advanced', value: 1 },
  { id: 'adv2', label: '边界条件', status: 'locked', category: 'advanced', value: 1 },
  { id: 'exp1', label: '创新实践', status: 'locked', category: 'expert', value: 1 },
]

const DEFAULT_LINKS: KnowledgeLink[] = [
  { source: 'root', target: 'basic1', strength: 0.9 },
  { source: 'root', target: 'basic2', strength: 0.85 },
  { source: 'basic1', target: 'inter1', strength: 0.7 },
  { source: 'basic2', target: 'inter1', strength: 0.75 },
  { source: 'inter1', target: 'inter2', strength: 0.8 },
  { source: 'inter1', target: 'adv1', strength: 0.6 },
  { source: 'inter2', target: 'adv1', strength: 0.65 },
  { source: 'adv1', target: 'adv2', strength: 0.7 },
  { source: 'adv2', target: 'exp1', strength: 0.5 },
]

export function KnowledgeConstellation({
  nodes: propNodes,
  links: propLinks,
  onNodeClick,
  className,
  height = 400
}: KnowledgeConstellationProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [hoverNode, setHoverNode] = useState<KnowledgeNode | null>(null)
  const [nodePositions, setNodePositions] = useState<Map<string, {x: number, y: number}>>(new Map())
  const [mounted, setMounted] = useState(false)

  const nodes = propNodes || DEFAULT_NODES
  const links = propLinks || DEFAULT_LINKS

  // 等待客户端挂载
  useEffect(() => {
    setMounted(true)
  }, [])

  // 计算智能布局 - 层次化同心圆
  useEffect(() => {
    if (!mounted || nodes.length === 0) return

    // 使用固定的 viewBox 坐标系 (0 0 600 400)
    const centerX = 300  // viewBox width / 2
    const centerY = 200  // viewBox height / 2

    const positions = new Map<string, {x: number, y: number}>()

    // 按状态分组节点
    const completedNodes = nodes.filter(n => n.status === 'completed')
    const inProgressNodes = nodes.filter(n => n.status === 'in-progress')
    const lockedNodes = nodes.filter(n => n.status === 'locked')

    // 动态计算布局
    const levels = [
      { radius: 0, nodes: completedNodes.slice(0, 1) },  // 核心层：第一个已完成节点
      { radius: 50, nodes: completedNodes.slice(1) },    // 内圈：其他已完成节点
      { radius: 90, nodes: inProgressNodes },            // 中圈：进行中节点
      { radius: 130, nodes: lockedNodes.slice(0, Math.ceil(lockedNodes.length / 2)) },  // 外圈1：部分锁定节点
      { radius: 160, nodes: lockedNodes.slice(Math.ceil(lockedNodes.length / 2)) }      // 外圈2：剩余锁定节点
    ]

    levels.forEach((level) => {
      if (level.nodes.length === 0) return

      const radius = level.radius

      level.nodes.forEach((node, index) => {
        if (radius === 0) {
          // 中心节点
          positions.set(node.id, { x: centerX, y: centerY })
        } else {
          // 圆周节点
          const angle = (index / level.nodes.length) * 2 * Math.PI - Math.PI / 2
          positions.set(node.id, {
            x: centerX + Math.cos(angle) * radius,
            y: centerY + Math.sin(angle) * radius * 0.8
          })
        }
      })
    })

    setNodePositions(positions)
  }, [mounted, nodes])

  // 根据状态获取节点颜色和发光效果
  const getNodeStyle = (node: KnowledgeNode) => {
    const colors = {
      completed: { fill: '#10B981', glow: 'rgba(16, 185, 129, 0.3)' },
      'in-progress': { fill: '#3B82F6', glow: 'rgba(59, 130, 246, 0.2)' },
      locked: { fill: '#D1D5DB', glow: 'transparent' }
    }
    return colors[node.status]
  }

  const legend = [
    { status: 'completed', label: '已掌握', color: '#10B981' },
    { status: 'in-progress', label: '学习中', color: '#3B82F6' },
    { status: 'locked', label: '未解锁', color: '#D1D5DB' }
  ]

  return (
    <div className={className}>
      {/* 标题区域 */}
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-black">知识星座</h3>
        <p className="text-sm text-gray-500 mt-1">
          知识图谱 · 层次化网络 · 动态交互
        </p>
      </div>

      {/* 图例 */}
      <div className="flex gap-3 mb-4 text-xs">
        {legend.map((item) => (
          <div key={item.status} className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-gray-50">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }} />
            <span className="text-gray-600">{item.label}</span>
          </div>
        ))}
      </div>

      {/* 图表容器 */}
      {mounted ? (
        <div
          ref={containerRef}
          className="w-full bg-white border border-gray-200 rounded-2xl overflow-hidden relative"
          style={{ height: `${height}px` }}
        >
          <svg
            ref={svgRef}
            width="100%"
            height="100%"
            viewBox="0 0 600 400"
            preserveAspectRatio="xMidYMid meet"
            style={{ position: 'absolute', top: 0, left: 0 }}
          >
            <defs>
              {/* 箭头标记 */}
              <marker
                id="arrow"
                viewBox="0 0 10 10"
                refX="8"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto"
              >
                <path d="M0,0 L8,5 L0,10" fill="rgba(0, 0, 0, 0.1)" />
              </marker>

              {/* 节点发光滤镜 */}
              <filter id="glow-completed" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feFlood floodColor="#10B981" floodOpacity="0.3" result="glowColor" />
                <feComposite in="glowColor" in2="blur" operator="in" result="softGlow" />
                <feMerge>
                  <feMergeNode in="softGlow" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>

              <filter id="glow-progress" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="2" result="blur" />
                <feFlood floodColor="#3B82F6" floodOpacity="0.25" result="glowColor" />
                <feComposite in="glowColor" in2="blur" operator="in" result="softGlow" />
                <feMerge>
                  <feMergeNode in="softGlow" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* 连线 */}
            {links.map((link, i) => {
              const sourcePos = nodePositions.get(link.source)
              const targetPos = nodePositions.get(link.target)
              if (!sourcePos || !targetPos) return null

              return (
                <motion.line
                  key={i}
                  initial={{ pathLength: 0, opacity: 0 }}
                  animate={{ pathLength: 1, opacity: 1 }}
                  transition={{ duration: 0.8, delay: i * 0.1 }}
                  x1={sourcePos.x}
                  y1={sourcePos.y}
                  x2={targetPos.x}
                  y2={targetPos.y}
                  stroke="rgba(0, 0, 0, 0.04)"
                  strokeWidth={link.strength * 1.5}
                  strokeLinecap="round"
                  markerEnd="url(#arrow)"
                />
              )
            })}

            {/* 节点 */}
            {nodes.map((node, i) => {
              const pos = nodePositions.get(node.id)
              if (!pos) return null

              const size = (node.value || 1) * 7
              const style = getNodeStyle(node)
              const isHovered = hoverNode?.id === node.id

              return (
                <motion.g
                  key={node.id}
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ duration: 0.4, delay: i * 0.08 }}
                  style={{ cursor: 'pointer' }}
                  onMouseEnter={() => setHoverNode(node)}
                  onMouseLeave={() => setHoverNode(null)}
                  onClick={() => onNodeClick?.(node)}
                >
                  {/* 外发光（已完成节点） */}
                  {node.status === 'completed' && (
                    <circle
                      cx={pos.x}
                      cy={pos.y}
                      r={size * 1.5}
                      fill={style.glow}
                      opacity={0.6}
                    />
                  )}

                  {/* 主圆圈 */}
                  <circle
                    cx={pos.x}
                    cy={pos.y}
                    r={isHovered ? size * 1.1 : size}
                    fill={style.fill}
                    stroke={isHovered ? '#000' : 'rgba(255, 255, 255, 0.9)'}
                    strokeWidth={isHovered ? 2 : 1}
                  />

                  {/* 内圈（进行中节点） */}
                  {node.status === 'in-progress' && (
                    <circle
                      cx={pos.x}
                      cy={pos.y}
                      r={size * 0.4}
                      fill="none"
                      stroke="rgba(255, 255, 255, 0.5)"
                      strokeWidth={1}
                    />
                  )}

                  {/* 标签 */}
                  <text
                    x={pos.x}
                    y={pos.y + size + 10}
                    textAnchor="middle"
                    fontSize={10}
                    fontFamily="Inter, sans-serif"
                    fontWeight={isHovered ? 500 : 400}
                    fill={node.status === 'locked' ? '#9CA3AF' : '#1F2937'}
                    pointerEvents="none"
                  >
                    {node.label}
                  </text>
                </motion.g>
              )
            })}
          </svg>
        </div>
      ) : (
        <div
          className="w-full bg-gray-50 border border-gray-200 rounded-2xl flex items-center justify-center"
          style={{ height: `${height}px` }}
        >
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-black"></div>
        </div>
      )}

      {/* 悬停信息卡片 */}
      {hoverNode && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-4 p-4 bg-white border border-gray-200 rounded-xl shadow-sm"
        >
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center"
                style={{
                  backgroundColor: legend.find(l => l.status === hoverNode.status)?.color
                }}
              >
                {hoverNode.status === 'completed' && (
                  <span className="text-white text-xs">✓</span>
                )}
              </div>
              <div>
                <h4 className="font-semibold text-sm">{hoverNode.label}</h4>
                <p className="text-xs text-gray-500 mt-0.5">
                  {legend.find(l => l.status === hoverNode.status)?.label}
                </p>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* 简化的统计信息 */}
      <div className="mt-4 flex justify-center gap-6">
        {[
          { count: nodes.filter(n => n.status === 'completed').length, label: '已掌握', color: 'text-emerald-600 bg-emerald-50 border-emerald-100' },
          { count: nodes.filter(n => n.status === 'in-progress').length, label: '学习中', color: 'text-blue-600 bg-blue-50 border-blue-100' },
          { count: nodes.filter(n => n.status === 'locked').length, label: '未解锁', color: 'text-gray-600 bg-gray-50 border-gray-200' }
        ].map((stat, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: i * 0.05 }}
            className="flex flex-col items-center gap-1 px-4 py-2 rounded-xl border text-center"
            style={{
              backgroundColor: stat.color.split(' ')[1] || '#F9FAFB',
              borderColor: stat.color.split(' ')[2] || '#E5E7EB'
            }}
          >
            <span className={`text-2xl font-semibold ${stat.color.split(' ')[0]}`}>
              {stat.count}
            </span>
            <span className="text-xs text-gray-600">{stat.label}</span>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
