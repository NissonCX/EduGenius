# 测试设置指南

## 概述

EduGenius 使用 Vitest 作为测试框架，配合 Testing Library 进行组件测试。

---

## 现有测试文件

| 文件 | 测试内容 | 状态 |
|------|----------|------|
| `src/lib/__tests__/cache.test.ts` | 缓存模块 | ✅ 已创建 |
| `src/lib/__tests__/config.test.ts` | 配置工具函数 | ✅ 已创建 |

---

## 安装测试依赖

```bash
# 安装测试依赖
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event @vitest/ui jsdom

# 安装 TypeScript 类型
npm install --save-dev @vitest/ui
```

---

## 配置文件

### vitest.config.ts

创建项目根目录的 `vitest.config.ts`：

```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData.ts'
      ]
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
})
```

### src/test/setup.ts

创建测试设置文件：

```typescript
import { expect, afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

// 扩展 Vitest 的 expect
expect.extend(matchers)

// 每个测试后清理
afterEach(() => {
  cleanup()
})
```

---

## 更新 package.json

添加测试脚本：

```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage",
    "test:run": "vitest run"
  }
}
```

---

## 测试文件结构

```
src/
├── lib/
│   ├── __tests__/
│   │   ├── cache.test.ts
│   │   ├── config.test.ts
│   │   └── latex-processor.test.ts  # 待添加
├── components/
│   ├── __tests__/
│   │   ├── Button.test.tsx
│   │   ├── Input.test.tsx
│   │   └── Skeleton.test.tsx
└── test/
    ├── setup.ts
    └── utils.tsx
```

---

## 编写测试

### 工具函数测试示例

```typescript
// src/lib/__tests__/latex-processor.test.ts
import { describe, it, expect } from 'vitest'
import { processLatexInMarkdown } from '../latex-processor'

describe('LaTeX 处理器', () => {
  it('应该转换行内 LaTeX', () => {
    const input = '这是 $x^2$ 公式'
    const output = processLatexInMarkdown(input)
    expect(output).toContain('$$x^2$$')
  })

  it('应该转换块级 LaTeX', () => {
    const input = '\\[ \\int_0^1 x dx \\]'
    const output = processLatexInMarkdown(input)
    expect(output).toContain('$$\\int_0^1 x dx$$')
  })
})
```

### 组件测试示例

```typescript
// src/components/__tests__/Button.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from '../ui/Button'

describe('Button 组件', () => {
  it('应该渲染按钮文本', () => {
    render(<Button>点击我</Button>)
    expect(screen.getByText('点击我')).toBeInTheDocument()
  })

  it('应该响应点击事件', async () => {
    const handleClick = vi.fn()
    const user = userEvent.setup()

    render(<Button onClick={handleClick}>点击我</Button>)

    await user.click(screen.getByText('点击我'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('应该在禁用状态下不响应点击', async () => {
    const handleClick = vi.fn()
    const user = userEvent.setup()

    render(
      <Button onClick={handleClick} disabled>
        点击我
      </Button>
    )

    await user.click(screen.getByText('点击我'))
    expect(handleClick).not.toHaveBeenCalled()
  })
})
```

---

## 测试命令

### 运行所有测试

```bash
npm test
```

### 监视模式

```bash
npm test -- --watch
```

### UI 模式

```bash
npm run test:ui
```

### 生成覆盖率报告

```bash
npm run test:coverage
```

---

## 测试覆盖率目标

| 类型 | 目标覆盖率 |
|------|-----------|
| 语句覆盖率 (Statements) | > 70% |
| 分支覆盖率 (Branches) | > 60% |
| 函数覆盖率 (Functions) | > 70% |
| 行覆盖率 (Lines) | > 70% |

---

## 常见问题

### 1. 测试环境错误

**问题**: `ReferenceError: document is not defined`

**解决方案**: 确保 `vitest.config.ts` 中设置了 `environment: 'jsdom'`

### 2. 导入路径错误

**问题**: `Cannot find module '@/components/...'`

**解决方案**: 检查 `vitest.config.ts` 中的 `resolve.alias` 配置

### 3. Mock 问题

**问题**: 需要模拟 API 请求

**解决方案**: 使用 `vi.fn()` 创建 mock 函数

```typescript
import { vi } from 'vitest'

const mockFetch = vi.fn().mockResolvedValue({
  ok: true,
  json: async () => ({ data: 'test' })
})

global.fetch = mockFetch
```

---

## 待添加的测试

### 高优先级

- [ ] `src/lib/latex-processor.test.ts` - LaTeX 处理
- [ ] `src/lib/errors.test.ts` - 错误处理
- [ ] `src/components/ui/Button.test.tsx` - 按钮组件
- [ ] `src/components/ui/Input.test.tsx` - 输入框组件

### 中优先级

- [ ] `src/components/ui/Skeleton.test.tsx` - 骨架屏组件
- [ ] `src/lib/api-client.test.ts` - API 客户端
- [ ] `src/contexts/AuthContext.test.tsx` - 认证上下文

### 低优先级

- [ ] `src/components/quiz/Quiz.test.tsx` - 测验组件
- [ ] `src/components/chat/ChatMessage.test.tsx` - 聊天消息组件

---

## CI/CD 集成

在 GitHub Actions 中添加测试步骤：

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm ci
      - run: npm run test:run
      - uses: codecov/codecov-action@v3
        with:
          files: ./coverage/coverage-final.json
```

---

**文档版本**: v1.0.0
**更新时间**: 2026-02-10
**适用版本**: EduGenius v1.0.0+
