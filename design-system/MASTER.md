# EduGenius 设计系统

## 产品定位
**类型**: 教育科技 SaaS 平台
**关键词**: 专业、智能、学习、知识
**目标用户**: 学生、教师、自学者

## 设计风格
**主风格**: Glassmorphism + Minimalism
- 干净现代的界面
- 玻璃态卡片提升质感
- 清晰的信息层次
- 流畅的动画过渡

## 颜色系统
```css
/* 主色调 */
--primary: #000000      /* 黑色 - 专业、权威 */
--primary-light: #1F2937 /* 深灰 - 柔和 */

/* 功能色 */
--success: #10B981      /* 绿色 - 成功/完成 */
--processing: #3B82F6   /* 蓝色 - 处理中 */
--warning: #F59E0B      /* 橙色 - 警告 */
--error: #EF4444        /* 红色 - 错误 */

/* 中性色 */
--bg-primary: #FFFFFF   /* 白色背景 */
--bg-secondary: #F9FAFB /* 浅灰背景 */
--text-primary: #111827  /* 深灰文本 */
--text-secondary: #6B7280 /* 次要文本 */
--border: #E5E7EB       /* 边框 */
```

## 字体系统
```css
/* 标题 */
font-heading: 'Inter', sans-serif
  - font-weight: 600-700
  - line-height: 1.2

/* 正文 */
font-body: 'Inter', sans-serif
  - font-weight: 400-500
  - line-height: 1.6
  - font-size: 16px
```

## 组件规范

### 玻璃态卡片
```css
.glass-card {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
}
```

### 进度条
```css
.progress-bar {
  background: #E5E7EB;
  border-radius: 9999px;
  overflow: hidden;
}

.progress-fill {
  background: linear-gradient(90deg, #3B82F6, #10B981);
  transition: width 0.5s ease-out;
}
```

### 按钮
- 主按钮: 黑色背景 + 白色文字
- 次按钮: 白色背景 + 黑色边框
- 禁用: gray-300 背景 + 不可点击

## 动画时长
- 微交互: 150ms
- 标准过渡: 200-300ms
- 页面切换: 300-400ms
- 进度条: 500ms ease-out

## 无障碍要求
- 对比度: 最小 4.5:1
- 触摸目标: 最小 44x44px
- 焦点状态: 清晰的 focus ring
- 加载状态: Skeleton 或 Spinner
