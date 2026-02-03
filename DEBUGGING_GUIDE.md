# 调试指南 - LaTeX 渲染问题

## 🔍 问题症状

- LaTeX 公式不能正常解析
- 每次需要刷新页面才能看到正确格式
- 流式输出完成后显示不正确

## ✅ 验证步骤

### 步骤 1：验证处理器函数

运行测试脚本：
```bash
node test-latex-processor.js
```

**期望结果：** 所有测试通过 ✅

**如果失败：** 处理器逻辑有问题，需要修复 `src/lib/latex-processor.ts`

### 步骤 2：清除所有缓存

```bash
# 1. 删除 Next.js 缓存
rm -rf .next

# 2. 删除 node_modules（可选，如果问题持续）
rm -rf node_modules
npm install

# 3. 重新构建
npm run build
```

### 步骤 3：清除浏览器缓存

**Chrome/Edge：**
1. 打开开发者工具（F12）
2. 右键点击刷新按钮
3. 选择"清空缓存并硬性重新加载"

**或者：**
- Windows: `Ctrl + Shift + Delete`
- Mac: `Cmd + Shift + Delete`
- 选择"缓存的图片和文件"
- 点击"清除数据"

### 步骤 4：检查开发模式

如果你在使用 `npm run dev`：

```bash
# 1. 停止开发服务器（Ctrl+C）
# 2. 清除缓存
rm -rf .next
# 3. 重新启动
npm run dev
```

### 步骤 5：检查浏览器控制台

1. 打开开发者工具（F12）
2. 切换到 Console 标签
3. 查找错误信息

**常见错误：**
- `Cannot find module '@/lib/latex-processor'` - 模块未找到
- `processLatexInMarkdown is not a function` - 导入错误
- KaTeX 相关错误 - CSS 未加载

### 步骤 6：检查网络面板

1. 打开开发者工具（F12）
2. 切换到 Network 标签
3. 刷新页面
4. 查找 `latex-processor` 相关的 JS 文件

**检查：**
- 文件是否成功加载（状态码 200）
- 文件大小是否正确（不是 0 字节）
- 文件内容是否包含最新代码

### 步骤 7：检查 React DevTools

1. 安装 React DevTools 扩展
2. 打开开发者工具
3. 切换到 Components 标签
4. 找到 `ChatMessage` 组件
5. 查看 props 和 state

**检查：**
- `message.content` 是否正确
- `processedContent` 是否包含 `$$`
- 组件是否重新渲染

## 🐛 常见问题和解决方案

### 问题 1：公式显示为纯文本

**症状：** `$$e^{i\pi} + 1 = 0$$` 显示为纯文本

**可能原因：**
1. KaTeX CSS 未加载
2. ReactMarkdown 配置错误
3. 处理器未运行

**解决方案：**
```bash
# 检查 KaTeX 是否安装
npm list katex

# 如果未安装或版本不对
npm install katex@^0.16.28 rehype-katex@^7.0.1 remark-math@^6.0.0
```

### 问题 2：刷新后才能看到正确格式

**症状：** 流式输出完成后显示不正确，刷新后正确

**可能原因：**
1. `StreamingMessage` 和 `ChatMessage` 使用不同的处理逻辑
2. React 没有检测到状态变化
3. 组件没有重新渲染

**解决方案：**
1. 确保两个组件都使用 `processLatexInMarkdown`
2. 检查 `useEffect` 依赖项
3. 添加调试日志

### 问题 3：某些公式能渲染，某些不能

**症状：** 行内公式 `$x$` 能渲染，但 `\(x\)` 不能

**可能原因：**
- 处理器没有转换 `\(` 和 `\)` 格式

**解决方案：**
检查 `src/lib/latex-processor.ts` 第 20-22 行：
```typescript
// 2. 转换 \( \) 格式为 $...$ （行内公式）
processed = processed.replace(/\\\(/g, '$')
processed = processed.replace(/\\\)/g, '$')
```

### 问题 4：开发模式正常，生产模式不正常

**症状：** `npm run dev` 正常，但 `npm run build` 后不正常

**可能原因：**
- 生产构建优化导致代码被错误处理
- 环境变量不同

**解决方案：**
```bash
# 清除构建缓存
rm -rf .next
rm -rf out

# 重新构建
npm run build

# 本地测试生产构建
npm start
```

## 🔧 调试代码

### 在 ChatMessage.tsx 中添加调试日志

```typescript
export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'
  
  const processedContent = React.useMemo(() => {
    if (isUser) return message.content
    
    const result = processLatexInMarkdown(message.content, false)
    
    // 调试日志
    console.log('=== ChatMessage 处理 ===')
    console.log('原始内容:', message.content.substring(0, 100))
    console.log('处理后:', result.substring(0, 100))
    console.log('包含 $$:', result.includes('$$'))
    
    return result
  }, [message.content, isUser])
  
  // ...
}
```

### 在 StreamingMessage.tsx 中添加调试日志

```typescript
export function StreamingMessage({ content, isComplete }: Props) {
  const renderContent = processLatexInMarkdown(content, !isComplete)
  
  // 调试日志
  console.log('=== StreamingMessage 处理 ===')
  console.log('原始内容:', content.substring(0, 100))
  console.log('处理后:', renderContent.substring(0, 100))
  console.log('包含 $$:', renderContent.includes('$$'))
  console.log('isComplete:', isComplete)
  
  // ...
}
```

### 在浏览器控制台测试

打开浏览器控制台，运行：

```javascript
// 测试处理器是否可用
const test = '$$e^{i\\pi} + 1 = 0$$'
console.log('测试输入:', test)

// 如果能访问到处理器
// import { processLatexInMarkdown } from '@/lib/latex-processor'
// console.log('处理后:', processLatexInMarkdown(test, false))
```

## 📋 检查清单

在报告问题前，请确认：

- [ ] 已运行 `node test-latex-processor.js`，所有测试通过
- [ ] 已清除 `.next` 目录
- [ ] 已清除浏览器缓存
- [ ] 已硬刷新页面（Ctrl+Shift+R）
- [ ] 已检查浏览器控制台，无错误
- [ ] 已检查网络面板，所有文件加载成功
- [ ] 已重启开发服务器（如果使用 `npm run dev`）
- [ ] 已尝试在隐身模式下打开

## 🆘 如果问题仍然存在

请提供以下信息：

1. **浏览器控制台的完整错误信息**
2. **网络面板的截图**（显示加载的 JS 文件）
3. **React DevTools 的截图**（显示 ChatMessage 组件的 props）
4. **具体的输入和输出**
   - 输入：AI 返回的原始内容
   - 输出：浏览器显示的内容
   - 期望：应该显示的内容
5. **运行模式**：开发模式（`npm run dev`）还是生产模式（`npm run build` + `npm start`）

## 🎯 快速修复尝试

如果上述步骤都不行，尝试这个"核弹"方案：

```bash
# 1. 完全清除
rm -rf .next
rm -rf node_modules
rm -rf package-lock.json

# 2. 重新安装
npm install

# 3. 重新构建
npm run build

# 4. 清除浏览器所有数据
# 在浏览器设置中清除所有缓存、Cookie、本地存储

# 5. 重启浏览器

# 6. 访问应用
npm start
```

---

**文档版本**: v1.1.0
**更新时间**: 2026-02-03
**状态**: LaTeX 渲染问题已修复，对话记忆功能正常
