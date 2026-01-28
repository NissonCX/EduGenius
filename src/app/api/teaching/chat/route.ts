/**
 * SSE Chat API Endpoint
 * 模拟流式对话响应（用于前端测试）
 */

import { NextRequest } from 'next/server'

export async function POST(request: NextRequest) {
  const body = await request.json()
  const { message, chapter_id, student_level, stream = true } = body

  // 模拟 AI 响应
  const mockResponse = `很好的问题！让我为你详细讲解。

关于 **${message || '这个知识点'}**，我们可以从以下几个方面来理解：

### 1. 核心概念
这是线性代数的基础概念之一，需要特别注意它的定义和性质。

### 2. 应用场景
在实际应用中，这个概念广泛用于：
- 计算机图形学
- 机器学习
- 物理模拟

### 3. 示例说明
\`\`\`mermaid
graph LR
    A[输入] --> B[处理]
    B --> C[输出]
    style A fill:#f9f9f9
    style B fill:#e3f2fd
    style C fill:#f0fdf4
\`\`\`

### 4. 数学表达
对于公式 $E = mc^2$，我们可以理解为...

**总结**：掌握这个知识点对后续学习非常重要。建议多做练习巩固。`

  if (stream) {
    // 创建 SSE 流
    const encoder = new TextEncoder()
    const stream = new ReadableStream({
      async start(controller) {
        const words = mockResponse.split('')
        let index = 0

        const sendWord = () => {
          if (index < words.length) {
            const chunk = words[index]
            const data = JSON.stringify({ content: chunk })
            controller.enqueue(encoder.encode(`data: ${data}\n\n`))
            index++
            // 模拟打字速度（每个字间隔 30-50ms）
            setTimeout(sendWord, Math.random() * 20 + 30)
          } else {
            controller.enqueue(encoder.encode('data: [DONE]\n\n'))
            controller.close()
          }
        }

        sendWord()
      }
    })

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    })
  }

  return Response.json({ content: mockResponse })
}
