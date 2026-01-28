# EduGenius 设计系统规范

> **核心理念**: Zen, Minimalist, White-space, Thin-line, Fluid-motion, International-standard

---

## 1. 视觉风格：极致的"无感"设计

### 色调方案
```css
/* 主色调 - 纯白体系 */
--bg-primary: #FFFFFF;
--bg-secondary: #F9FAFB;  /* 极浅灰背景块 */
--bg-tertiary: #F3F4F6;   /* 气泡区分 */

/* 文字色彩 - 深灰而非纯黑 */
--text-primary: #111827;     /* 主文字 */
--text-secondary: #6B7280;   /* 次要文字 */
--text-tertiary: #9CA3AF;    /* 辅助文字 */

/* 强调色 - 单色调低饱和 */
--accent-default: rgba(0, 0, 0, 0.06);  /* 黑色6%透明度 */
--accent-hover: rgba(0, 0, 0, 0.08);     /* 悬停8%透明度 */
--accent-active: rgba(0, 0, 0, 0.12);    /* 激活12%透明度 */

/* 边框色彩 - 极细接近背景 */
--border-default: #E5E7EB;      /* 默认边框 */
--border-subtle: #F3F4F6;        /* 微妙边框 */
--border-hover: #D1D5DB;         /* 悬停边框 */
```

### 线条与边框规范
```css
/* 极细边框体系 */
.border-thin {
  border-width: 0.5px;
  border-style: solid;
}

.border-standard {
  border-width: 1px;
  border-style: solid;
}

/* 悬停时加深 */
.hoverable-border {
  transition: border-color 0.2s ease;
}

.hoverable-border:hover {
  border-color: var(--border-hover);
}
```

### 负空间（Negative Space）
```css
/* 组件间距 - "呼吸感" */
.spacing-xs { margin: 0.25rem; }  /* 4px */
.spacing-sm { margin: 0.5rem; }   /* 8px */
.spacing-md { margin: 1rem; }     /* 16px */
.spacing-lg { margin: 1.5rem; }    /* 24px */
.spacing-xl { margin: 2rem; }     /* 32px */
.spacing-2xl { margin: 3rem; }    /* 48px */

/* 行距 - 宽裕感 */
.leading-tight { line-height: 1.25; }
.leading-normal { line-height: 1.5; }
-leading-relaxed { line-height: 1.75; }
.leading-loose { line-height: 2; }
```

---

## 2. 交互体验：丝滑的"情绪反馈"

### 动效哲学
```typescript
// Framer Motion 配置
const springConfig = {
  type: "spring",
  stiffness: 300,        // 柔和弹性
  damping: 25,           // 自然阻尼
  mass: 0.8             // 轻量级运动
}

const easeConfig = {
  duration: 0.3,
  ease: [0.25, 0.1, 0.25, 1]  // 自然缓动曲线
}
```

### 流光进度条
```tsx
<motion.div
  className="h-full bg-black rounded-full overflow-hidden"
  initial={{ width: 0 }}
  animate={{ width: `${progress}%` }}
  transition={{ duration: 0.8, ease: "easeOut" }}
>
  {/* 流光效果 */}
  <motion.div
    className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
    animate={{ x: ['-100%', '100%'] }}
    transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
  />
</motion.div>
```

### 微交互规范

#### 1. 错误颤动
```tsx
<motion.div
  initial={false}
  animate={hasError ? {
    x: [0, -5, 5, -5, 5, -3, 3, 0],
    transition: { duration: 0.4 }
  } : false}
>
  <AlertCircle className="text-red-500" />
</motion.div>
```

#### 2. 成功光斑
```tsx
<motion.div
  className="absolute inset-0"
  initial={{ scale: 0, opacity: 0.5 }}
  animate={{ scale: 2, opacity: 0 }}
  transition={{ duration: 0.6, ease: "easeOut" }}
>
  <div className="w-2 h-2 bg-emerald-400 rounded-full" />
</motion.div>
```

#### 3. 侧边栏折叠动画
```tsx
<motion.aside
  animate={{ width: isExpanded ? 240 : 64 }}
  transition={{ type: "spring", stiffness: 300, damping: 25 }}
>
  {/* 侧边栏内容 */}
</motion.aside>
```

### 响应式输入框
```tsx
<textarea
  className="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl resize-none
             focus:outline-none focus:ring-1 focus:ring-black/5
             transition-all duration-200
             rows={1}
  />
```

---

## 3. 数据可视化：将逻辑"实体化"

### 能力雷达图 (Competency Radar)

#### 设计规范
```css
/* 极细线条，半透明填充 */
.radar-axis-line {
  stroke: #E5E7EB;
  stroke-width: 0.5;
}

.radar-polygon {
  fill: rgba(0, 0, 0, 0.03);      /* 单色调极浅填充 */
  stroke: rgba(0, 0, 0, 0.3);     /* 深色描边 */
  stroke-width: 1;
  fill-opacity: 0.6;
}

.radar-point {
  fill: #111827;
  r: 2;
}
```

#### 交互规范
- 点击维度 → 筛选相关题目
- 悬停节点 → 显示详细数值
- 切换数据 → 平滑过渡动画

#### 实现代码
```tsx
<RadarChart data={competencyData}>
  <PolarGrid stroke="#E5E7EB" strokeWidth={0.5} />
  <PolarAngleAxis
    tick={{ fill: '#6B7280', fontSize: 11 }}
  />
  <Radar
    name="能力值"
    dataKey="value"
    fill="rgba(0, 0, 0, 0.03)"
    stroke="rgba(0, 0, 0, 0.3)"
    strokeWidth={1}
    dot={{ r: 2 }}
    animationBegin={0}
    animationDuration={800}
  />
</RadarChart>
```

### 知识星座图 (Knowledge Constellation)

#### 设计规范
```css
/* 节点 */
.node-circle {
  fill: #FFFFFF;
  stroke: #111827;
  stroke-width: 1;
  r: 6;
}

.node-completed {
  stroke: #10B981;        /* 完成节点 - 绿色 */
}

/* 连接线 */
.link-line {
  stroke: #E5E7EB;
  stroke-width: 0.5;
  opacity: 0.6;
}

/* 脉冲动画 */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.node-pulse {
  animation: pulse 3s ease-in-out infinite;
}
```

#### 实现代码框架
```tsx
import { useEffect, useRef } from 'react'
import * as d3 from 'd3'

const KnowledgeConstellation = ({ nodes, links }) => {
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    const svg = d3.select(svgRef.current)
    const width = 400
    const height = 400

    // 创建力导向模拟
    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(d => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-200))
      .force("center", d3.forceCenter(width / 2, height / 2))

    // 绘制连接线
    const link = svg.append("g")
      .selectAll("line")
      .data(links)
      .enter()
      .append("line")
      .attr("stroke", "#E5E7EB")
      .attr("stroke-width", 0.5)

    // 绘制节点
    const node = svg.append("g")
      .selectAll("circle")
      .data(nodes)
      .enter()
      .append("circle")
      .attr("class", d => `node-circle ${d.completed ? 'node-completed node-pulse' : ''}`)
      .attr("r", 6)
      .attr("fill", "#FFFFFF")
      .attr("stroke", "#111827")
      .attr("stroke-width", 1)

    simulation.on("tick", () => {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y)

      node
        .attr("cx", d => d.x)
        .attr("cy", d => d.y)
    })

    return () => {
      simulation.stop()
    }
  }, [nodes, links])

  return <svg ref={svgRef} width={400} height={400} />
}
```

---

## 4. 功能布局：沉浸式学习空间

### 仪表盘 (Dashboard)
```tsx
{/* 模块化 Card 布局 */}
<div className="grid grid-cols-1 md:grid-cols-3 gap-6">
  {/* 统计卡片 */}
  <div className="p-6 bg-white border border-gray-100 rounded-2xl">
    <p className="text-sm text-gray-600">完成章节</p>
    <p className="text-3xl font-light text-gray-900">8/12</p>
  </div>
</div>
```

### 学习界面 (Study Workspace)
```tsx
{/* 分屏设计 */}
<div className="flex h-screen bg-white">
  {/* 左侧：对话流 */}
  <div className="flex-1 border-r border-gray-100">
    {/* 极简对话 */}
  </div>

  {/* 右侧：动态内容 */}
  <div className="w-96">
    {/* 思维导图或PDF高亮 */}
  </div>
</div>
```

### 浮动工具栏设计
```tsx
{/* 像音量键一样精美的滑块 */}
<div className="absolute bottom-6 right-6">
  <div className="p-3 bg-white border border-gray-100 rounded-2xl shadow-sm">
    <label className="text-xs text-gray-500 mb-2">导师风格</label>
    <input
      type="range"
      min="1"
      max="5"
      step="1"
      className="w-full h-1 bg-gray-100 rounded-full appearance-none
                 [&::-webkit-slider-thumb]:appearance-none
                 [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4
                 [&::-webkit-slider-thumb]:rounded-full
                 [&::-webkit-slider-thumb]:bg-gray-900"
    />
  </div>
</div>
```

---

## 5. 通用组件样式

### 按钮 (Button)
```tsx
// 主要按钮
<button className="px-6 py-3 bg-black text-white rounded-xl
                   hover:bg-gray-900 active:scale-[0.98]
                   transition-all duration-200
                   font-medium text-sm">
  按钮
</button>

// 次要按钮
<button className="px-6 py-3 border border-gray-200 text-gray-900 rounded-xl
                   hover:bg-gray-50 active:scale-[0.98]
                   transition-all duration-200
                   font-medium text-sm">
  按钮
</button>

// 幽灵按钮
<button className="px-4 py-2 text-gray-600 hover:text-gray-900
                   hover:bg-gray-50 rounded-lg
                   transition-all duration-200
                   text-sm">
  按钮
</button>
```

### 卡片 (Card)
```tsx
<div className="p-6 bg-white border border-gray-100 rounded-2xl
            hover:shadow-sm transition-shadow duration-200">
  {/* 卡片内容 */}
</div>
```

### 输入框 (Input)
```tsx
<input
  className="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl
         focus:outline-none focus:ring-1 focus:ring-black/5
         focus:border-gray-300
         transition-all duration-200
         placeholder:text-gray-400
         text-sm"
/>
```

---

## 6. 动画常量库

```typescript
// constants/animations.ts
export const animations = {
  // 入场动画
  fadeIn: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    transition: { duration: 0.3 }
  },

  // 滑入动画
  slideIn: {
    initial: { x: -20, opacity: 0 },
    animate: { x: 0, opacity: 1 },
    transition: { duration: 0.3, ease: "easeOut" }
  },

  // 缩放动画
  scaleIn: {
    initial: { scale: 0.95, opacity: 0 },
    animate: { scale: 1, opacity: 1 },
    transition: { duration: 0.2, ease: "easeOut" }
  },

  // 弹性动画
  spring: {
    type: "spring",
    stiffness: 300,
    damping: 25,
    mass: 0.8
  }
}

export const transitions = {
  default: {
    type: "tween",
    ease: [0.25, 0.1, 0.25, 1],
    duration: 0.3
  },
  fluid: {
    type: "spring",
    stiffness: 300,
    damping: 25,
    mass: 0.8
  }
}
```

---

## 7. 响应式断点

```css
/* 断点系统 */
@media (max-width: 640px) {  /* 移动端 */
  .container { padding: 1rem; }
  .grid { grid-template-columns: 1fr; }
}

@media (max-width: 768px) {  /* 平板 */
  .sidebar { display: none; }
}

@media (max-width: 1024px) {  /* 小屏笔记本 */
  .grid { grid-template-columns: repeat(2, 1fr); }
}
```

---

## 8. 设计检查清单

### 视觉
- [ ] 纯白底色 (#FFFFFF)
- [ ] 深灰文字 (#111827) 非纯黑
- [ ] 极细边框 (0.5px - 1px)
- [ ] 充足的负空间
- [ ] 单色调低饱和度色彩

### 交互
- [ ] 流光进度条
- [ ] 平滑的过渡动画
- [ ] 微交互反馈
- [ ] 响应式输入框

### 数据可视化
- [ ] 能力雷达图使用极细线条
- [ ] 知识星座图有脉冲效果
- [ ] 可交互的图表

### 布局
- [ ] 模块化卡片布局
- [ ] 分屏学习界面
- [ ] 浮动工具栏

---

*最后更新: 2026-01-28*
*遵循此设计系统实现所有新功能和组件*
