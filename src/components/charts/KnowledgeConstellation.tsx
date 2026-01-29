'use client'

/**
 * KnowledgeConstellation - 知识星座图组件（增强版）
 * 功能：
 * - 节点展开/收起子节点
 * - 搜索和过滤功能
 * - 详细信息tooltip
 * - 移动端适配
 * - 连线强度可视化
 */

import { useEffect, useRef, useState, useMemo } from 'react'
import { Search, Filter, ChevronDown, ChevronUp, BookOpen, Clock, Lock } from 'lucide-react'

interface KnowledgeNode {
  id: string
  label: string
  status: 'completed' | 'in-progress' | 'locked'
  category: string
  value?: number
  children?: KnowledgeNode[]
  progress?: number
  timeSpent?: number
  description?: string
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

// 默认演示数据（带子节点和详细信息）
const DEFAULT_NODES: KnowledgeNode[] = [
  {
    id: 'root',
    label: '核心概念',
    status: 'completed',
    category: 'core',
    value: 3,
    progress: 100,
    timeSpent: 120,
    description: '基础知识的核心理论',
    children: [
      { id: 'root-1', label: '基础定义', status: 'completed', category: 'core', value: 1 },
      { id: 'root-2', label: '核心原理', status: 'completed', category: 'core', value: 1 }
    ]
  },
  {
    id: 'basic1',
    label: '基础理论',
    status: 'completed',
    category: 'basic',
    value: 2,
    progress: 100,
    timeSpent: 90,
    description: '基础理论知识框架',
    children: [
      { id: 'basic1-1', label: '概念A', status: 'completed', category: 'basic', value: 1 },
      { id: 'basic1-2', label: '概念B', status: 'completed', category: 'basic', value: 1 }
    ]
  },
  {
    id: 'basic2',
    label: '定义与术语',
    status: 'completed',
    category: 'basic',
    value: 2,
    progress: 100,
    timeSpent: 60,
    description: '关键术语和定义',
  },
  {
    id: 'inter1',
    label: '应用场景',
    status: 'in-progress',
    category: 'intermediate',
    value: 2,
    progress: 65,
    timeSpent: 45,
    description: '实际应用场景分析',
    children: [
      { id: 'inter1-1', label: '场景1', status: 'in-progress', category: 'intermediate', value: 1 },
      { id: 'inter1-2', label: '场景2', status: 'locked', category: 'intermediate', value: 1 }
    ]
  },
  {
    id: 'inter2',
    label: '实际案例',
    status: 'in-progress',
    category: 'intermediate',
    value: 2,
    progress: 40,
    timeSpent: 30,
    description: '真实案例分析',
  },
  {
    id: 'adv1',
    label: '高级应用',
    status: 'locked',
    category: 'advanced',
    value: 1,
    description: '需要掌握前置知识',
  },
  {
    id: 'adv2',
    label: '边界条件',
    status: 'locked',
    category: 'advanced',
    value: 1,
    description: '需要掌握前置知识',
  },
  {
    id: 'exp1',
    label: '创新实践',
    status: 'locked',
    category: 'expert',
    value: 1,
    description: '高级内容，需要全面掌握',
  },
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
  const [searchQuery, setSearchQuery] = useState('')
  const [filterStatus, setFilterStatus] = useState<'all' | 'completed' | 'in-progress' | 'locked'>('all')
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())
  const [showSearch, setShowSearch] = useState(false)
  const [isMobile, setIsMobile] = useState(false)

  const nodes = propNodes || DEFAULT_NODES
  const links = propLinks || DEFAULT_LINKS

  // 检测移动端
  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768)
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // 等待客户端挂载
  useEffect(() => {
    setMounted(true)
  }, [])

  // 过滤和搜索节点
  const filteredNodes = useMemo(() => {
    return nodes.filter(node => {
      const matchesStatus = filterStatus === 'all' || node.status === filterStatus
      const matchesSearch = searchQuery === '' ||
        node.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
        node.description?.toLowerCase().includes(searchQuery.toLowerCase())
      return matchesStatus && matchesSearch
    })
  }, [nodes, filterStatus, searchQuery])

  // 计算智能布局 - 层次化同心圆
  useEffect(() => {
    if (!mounted || filteredNodes.length === 0) return

    // 使用固定的 viewBox 坐标系 (0 0 600 400)
    const centerX = 300
    const centerY = 200

    const positions = new Map<string, {x: number, y: number}>()

    // 按状态分组节点
    const completedNodes = filteredNodes.filter(n => n.status === 'completed')
    const inProgressNodes = filteredNodes.filter(n => n.status === 'in-progress')
    const lockedNodes = filteredNodes.filter(n => n.status === 'locked')

    // 动态计算布局
    const levels = [
      { radius: 0, nodes: completedNodes.slice(0, 1) },
      { radius: 50, nodes: completedNodes.slice(1) },
      { radius: 90, nodes: inProgressNodes },
      { radius: 130, nodes: lockedNodes.slice(0, Math.ceil(lockedNodes.length / 2)) },
      { radius: 160, nodes: lockedNodes.slice(Math.ceil(lockedNodes.length / 2)) }
    ]

    levels.forEach((level) => {
      if (level.nodes.length === 0) return

      const radius = level.radius

      level.nodes.forEach((node, index) => {
        if (radius === 0) {
          positions.set(node.id, { x: centerX, y: centerY })
        } else {
          const angle = (index / level.nodes.length) * 2 * Math.PI - Math.PI / 2
          positions.set(node.id, {
            x: centerX + Math.cos(angle) * radius,
            y: centerY + Math.sin(angle) * radius * 0.8
          })
        }
      })
    })

    setNodePositions(positions)
  }, [mounted, filteredNodes])

  // 切换节点展开状态
  const toggleNodeExpansion = (nodeId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setExpandedNodes(prev => {
      const newSet = new Set(prev)
      if (newSet.has(nodeId)) {
        newSet.delete(nodeId)
      } else {
        newSet.add(nodeId)
      }
      return newSet
    })
  }

  // 根据状态获取节点颜色
  const getNodeStyle = (node: KnowledgeNode) => {
    const colors = {
      completed: { fill: '#000000', glow: 'rgba(0, 0, 0, 0.15)' },
      'in-progress': { fill: '#6B7280', glow: 'rgba(107, 114, 128, 0.15)' },
      locked: { fill: '#D1D5DB', glow: 'transparent' }
    }
    return colors[node.status]
  }

  const legend = [
    { status: 'completed', label: '已掌握', color: '#000000' },
    { status: 'in-progress', label: '学习中', color: '#6B7280' },
    { status: 'locked', label: '未解锁', color: '#D1D5DB' }
  ]

  return (
    <div className={className}>
      {/* 标题区域 */}
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-black">知识星座</h3>
            <p className="text-sm text-gray-500 mt-1">
              知识图谱 · 动态交互 · 进度追踪
            </p>
          </div>

          {/* 搜索和过滤按钮 */}
          <div className="flex gap-2">
            <button
              onClick={() => setShowSearch(!showSearch)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="搜索"
            >
              <Search className="w-4 h-4 text-gray-600" />
            </button>
            <button
              onClick={() => {
                const states: Array<'all' | 'completed' | 'in-progress' | 'locked'> = ['all', 'completed', 'in-progress', 'locked']
                const currentIndex = states.indexOf(filterStatus)
                setFilterStatus(states[(currentIndex + 1) % states.length])
              }}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="过滤"
            >
              <Filter className="w-4 h-4 text-gray-600" />
            </button>
          </div>
        </div>

        {/* 搜索框 */}
        {showSearch && (
          <div className="mt-3">
            <input
              type="text"
              placeholder="搜索知识点..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-black focus:border-transparent outline-none"
            />
          </div>
        )}

        {/* 过滤状态指示 */}
        {filterStatus !== 'all' && (
          <div className="mt-2 flex items-center gap-2">
            <span className="text-xs text-gray-600">当前过滤：</span>
            <button
              onClick={() => setFilterStatus('all')}
              className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-lg hover:bg-gray-200 transition-colors"
            >
              {legend.find(l => l.status === filterStatus)?.label} ×
            </button>
          </div>
        )}
      </div>

      {/* 图例 */}
      <div className="flex flex-wrap gap-2 mb-4 text-xs">
        {legend.map((item) => (
          <button
            key={item.status}
            onClick={() => setFilterStatus(item.status as any)}
            className={`flex items-center gap-1.5 px-2 py-1 rounded-full transition-colors ${
              filterStatus === item.status
                ? 'bg-black text-white'
                : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
            }`}
          >
            <div
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: filterStatus === item.status ? '#fff' : item.color }}
            />
            <span>{item.label}</span>
          </button>
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
                <feFlood floodColor="#000000" floodOpacity="0.15" result="glowColor" />
                <feComposite in="glowColor" in2="blur" operator="in" result="softGlow" />
                <feMerge>
                  <feMergeNode in="softGlow" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>

              <filter id="glow-progress" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="2" result="blur" />
                <feFlood floodColor="#6B7280" floodOpacity="0.2" result="glowColor" />
                <feComposite in="glowColor" in2="blur" operator="in" result="softGlow" />
                <feMerge>
                  <feMergeNode in="softGlow" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* 连线 - 根据强度显示不同粗细和透明度 */}
            {links.map((link, i) => {
              const sourcePos = nodePositions.get(link.source)
              const targetPos = nodePositions.get(link.target)
              if (!sourcePos || !targetPos) return null

              const lineWidth = Math.max(0.5, link.strength * 2)
              const opacity = Math.max(0.03, link.strength * 0.15)

              return (
                <line
                  key={`${link.source}-${link.target}`}
                  x1={sourcePos.x}
                  y1={sourcePos.y}
                  x2={targetPos.x}
                  y2={targetPos.y}
                  stroke={`rgba(0, 0, 0, ${opacity})`}
                  strokeWidth={lineWidth}
                  strokeLinecap="round"
                  markerEnd="url(#arrow)"
                />
              )
            })}

            {/* 节点 */}
            {filteredNodes.map((node, i) => {
              const pos = nodePositions.get(node.id)
              if (!pos) return null

              const size = (node.value || 1) * (isMobile ? 6 : 7)
              const style = getNodeStyle(node)
              const isHovered = hoverNode?.id === node.id
              const isExpanded = expandedNodes.has(node.id)
              const hasChildren = node.children && node.children.length > 0

              return (
                <g
                  key={node.id}
                  style={{ cursor: 'pointer' }}
                  onMouseEnter={() => setHoverNode(node)}
                  onMouseLeave={() => setHoverNode(null)}
                  onClick={(e) => {
                    if (hasChildren) {
                      toggleNodeExpansion(node.id, e)
                    }
                    onNodeClick?.(node)
                  }}
                >
                  {/* 已完成节点的脉冲效果 - 仅在悬停时显示 */}
                  {node.status === 'completed' && isHovered && (
                    <>
                      <circle
                        cx={pos.x}
                        cy={pos.y}
                        r={size * 1.5}
                        fill={style.glow}
                      />
                      <circle
                        cx={pos.x}
                        cy={pos.y}
                        r={size * 1.8}
                        fill="transparent"
                        stroke="rgba(0, 0, 0, 0.1)"
                        strokeWidth={1}
                      />
                    </>
                  )}

                  {/* 主圆圈 */}
                  <circle
                    cx={pos.x}
                    cy={pos.y}
                    r={isHovered ? size * 1.15 : size}
                    fill={style.fill}
                    stroke={isHovered ? '#000' : 'rgba(255, 255, 255, 0.9)'}
                    strokeWidth={isHovered ? 2 : 1}
                    style={{ transition: 'all 0.2s ease' }}
                  />

                  {/* 进行中节点的内圈 */}
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

                  {/* 展开指示器 */}
                  {hasChildren && (
                    <g
                      transform={`translate(${pos.x + size * 0.6}, ${pos.y - size * 0.6})`}
                    >
                      <circle
                        r={size * 0.35}
                        fill="white"
                        stroke="#E5E7EB"
                        strokeWidth={1}
                      />
                      {isExpanded ? (
                        <ChevronUp
                          width={size * 0.4}
                          height={size * 0.4}
                          x={-size * 0.2}
                          y={-size * 0.2}
                          color="#6B7280"
                        />
                      ) : (
                        <ChevronDown
                          width={size * 0.4}
                          height={size * 0.4}
                          x={-size * 0.2}
                          y={-size * 0.2}
                          color="#6B7280"
                        />
                      )}
                    </g>
                  )}

                  {/* 标签 */}
                  <text
                    x={pos.x}
                    y={pos.y + size + (isMobile ? 8 : 10)}
                    textAnchor="middle"
                    fontSize={isMobile ? 9 : 10}
                    fontFamily="Inter, sans-serif"
                    fontWeight={isHovered ? 500 : 400}
                    fill={node.status === 'locked' ? '#9CA3AF' : '#1F2937'}
                    pointerEvents="none"
                  >
                    {node.label}
                  </text>
                </g>
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

      {/* 增强的悬停信息卡片 */}
      {hoverNode && (
        <div className="mt-4 p-4 bg-white border border-gray-200 rounded-xl shadow-sm">
          <div className="flex items-start gap-3">
            <div
              className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
              style={{
                backgroundColor: legend.find(l => l.status === hoverNode.status)?.color + '20'
              }}
            >
              {hoverNode.status === 'completed' && (
                <span className="text-lg">✓</span>
              )}
              {hoverNode.status === 'in-progress' && (
                <BookOpen className="w-5 h-5" style={{ color: legend.find(l => l.status === 'in-progress')?.color }} />
              )}
              {hoverNode.status === 'locked' && (
                <Lock className="w-5 h-5 text-gray-400" />
              )}
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-base">{hoverNode.label}</h4>
              <p className="text-xs text-gray-500 mt-0.5">
                {legend.find(l => l.status === hoverNode.status)?.label}
              </p>
              {hoverNode.description && (
                <p className="text-sm text-gray-600 mt-2">{hoverNode.description}</p>
              )}

              {/* 进度和时间信息 */}
              <div className="mt-3 flex flex-wrap gap-4">
                {hoverNode.progress !== undefined && hoverNode.status === 'in-progress' && (
                  <div className="flex items-center gap-2 text-xs text-gray-600">
                    <div className="w-16 bg-gray-200 rounded-full h-1.5">
                      <div
                        className="bg-black h-1.5 rounded-full transition-all"
                        style={{ width: `${hoverNode.progress}%` }}
                      />
                    </div>
                    <span>{hoverNode.progress}%</span>
                  </div>
                )}
                {hoverNode.timeSpent && (
                  <div className="flex items-center gap-1 text-xs text-gray-600">
                    <Clock className="w-3 h-3" />
                    <span>{hoverNode.timeSpent} 分钟</span>
                  </div>
                )}
              </div>

              {/* 子节点列表 */}
              {hoverNode.children && hoverNode.children.length > 0 && (
                <div className="mt-3">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      toggleNodeExpansion(hoverNode.id, e)
                    }}
                    className="flex items-center gap-1 text-xs text-gray-600 hover:text-black transition-colors"
                  >
                    {expandedNodes.has(hoverNode.id) ? (
                      <ChevronUp className="w-3 h-3" />
                    ) : (
                      <ChevronDown className="w-3 h-3" />
                    )}
                    <span>{hoverNode.children.length} 个子知识点</span>
                  </button>
                  {expandedNodes.has(hoverNode.id) && (
                    <div className="mt-2 space-y-1 pl-2">
                      {hoverNode.children.map((child) => (
                        <div
                          key={child.id}
                          className="flex items-center gap-2 text-xs py-1 px-2 rounded bg-gray-50"
                        >
                          <div
                            className={`w-1.5 h-1.5 rounded-full ${
                              child.status === 'completed'
                                ? 'bg-black'
                                : child.status === 'in-progress'
                                ? 'bg-gray-400'
                                : 'bg-gray-300'
                            }`}
                          />
                          <span className="text-gray-700">{child.label}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 统计信息 */}
      <div className="mt-4 grid grid-cols-3 gap-2">
        {[
          { count: nodes.filter(n => n.status === 'completed').length, label: '已掌握', color: 'bg-black text-white' },
          { count: nodes.filter(n => n.status === 'in-progress').length, label: '学习中', color: 'bg-gray-100 text-gray-700' },
          { count: nodes.filter(n => n.status === 'locked').length, label: '未解锁', color: 'bg-gray-50 text-gray-600 border border-gray-200' }
        ].map((stat, i) => (
          <div
            key={i}
            className={`flex flex-col items-center gap-1 py-3 rounded-xl text-center ${stat.color}`}
          >
            <span className="text-xl font-semibold">{stat.count}</span>
            <span className="text-xs">{stat.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
