/**
 * LaTeX 处理器单元测试
 */

import { describe, it, expect } from 'vitest'
import { processLatexInMarkdown } from '../latex-processor'

describe('LaTeX 处理器', () => {
  describe('块级公式转换', () => {
    it('应该转换 \\[ \\] 为 $$...$$', () => {
      const input = '公式：\\[ E = mc^2 \\]'
      const result = processLatexInMarkdown(input)
      expect(result).toContain('$$\n  E = mc^2 \n$$')
    })

    it('应该处理多个 \\[ \\] 公式', () => {
      const input = '\\[ x^2 \\] 和 \\[ y^2 \\]'
      const result = processLatexInMarkdown(input)
      const mathBlocks = result.match(/\$\$/g)
      expect(mathBlocks).toHaveLength(4) // 2个公式，每个有2个$$
    })
  })

  describe('行内公式转换', () => {
    it('应该转换 \\( \\) 为 $...$', () => {
      const input = '这是 \\( x^2 \\) 公式'
      const result = processLatexInMarkdown(input)
      expect(result).toContain('$ x^2 $')
    })

    it('应该保持行内公式在文本中', () => {
      const input = '公式为 \\( E = mc^2 \\] 是爱因斯坦的质能方程'
      const result = processLatexInMarkdown(input)
      expect(result).toContain('公式为 $ E = mc^2 $ 是爱因斯坦的质能方程')
    })
  })

  describe('智能 LaTeX 识别', () => {
    it('应该识别包含下标的化学式', () => {
      const input = 'H_2O'
      const result = processLatexInMarkdown(input)
      expect(result).toContain('$$H_2O$$')
    })

    it('应该识别包含上标的公式', () => {
      const input = 'x^2 + y^2'
      const result = processLatexInMarkdown(input)
      expect(result).toContain('$$x^2 + y^2$$')
    })

    it('应该识别 LaTeX 命令', () => {
      const input = '\\text{Cu} + 2\\text{H}_2\\text{SO}_4'
      const result = processLatexInMarkdown(input)
      expect(result).toContain('$$\\text{Cu} + 2\\text{H}_2\\text{SO}_4$$')
    })

    it('应该识别化学方程式', () => {
      const input = '2\\,H_2O_2(aq) \\xrightarrow{MnO_2} 2\\,H_2O(l) + O_2(g)'
      const result = processLatexInMarkdown(input)
      expect(result).toContain('$$2\\,H_2O_2(aq) \\xrightarrow{MnO_2} 2\\,H_2O(l) + O_2(g)$$')
    })
  })

  describe('代码块保护', () => {
    it('不应该转换代码块中的内容', () => {
      const input = '```latex\nx^2\n```'
      const result = processLatexInMarkdown(input)
      expect(result).toContain('```latex\nx^2\n```')
    })

    it('不应该转换行内代码中的内容', () => {
      const input = '这是 `x^2` 代码'
      const result = processLatexInMarkdown(input)
      expect(result).not.toContain('$$x^2$$')
    })
  })

  describe('Markdown 语法保护', () => {
    it('不应该转换标题', () => {
      const input = '# 标题 x^2'
      const result = processLatexInMarkdown(input)
      expect(result).toBe('# 标题 x^2')
    })

    it('不应该转换列表项', () => {
      const input = '- 项目 H_2O'
      const result = processLatexInMarkdown(input)
      expect(result).toBe('- 项目 H_2O')
    })

    it('不应该转换数字列表', () => {
      const input = '1. 第一项 x^2'
      const result = processLatexInMarkdown(input)
      expect(result).toBe('1. 第一项 x^2')
    })
  })

  describe('已包裹公式保护', () => {
    it('不应该重复处理已经用 $$ 包裹的公式', () => {
      const input = '$$E = mc^2$$'
      const result = processLatexInMarkdown(input)
      expect(result).toBe('$$E = mc^2$$')
    })

    it('不应该重复处理已经用 $ 包裹的公式', () => {
      const input = '$x^2$'
      const result = processLatexInMarkdown(input)
      expect(result).toBe('$x^2$')
    })
  })

  describe('普通文本', () => {
    it('不应该处理普通文本', () => {
      const input = '这是一段普通文本'
      const result = processLatexInMarkdown(input)
      expect(result).toBe('这是一段普通文本')
    })

    it('不应该处理不包含 LaTeX 特征的文本', () => {
      const input = 'Hello World 123'
      const result = processLatexInMarkdown(input)
      expect(result).toBe('Hello World 123')
    })
  })

  describe('流式输出模式', () => {
    it('应该闭合未完成的代码块', () => {
      const input = '```javascript\nconsole.log("test")'
      const result = processLatexInMarkdown(input, true)
      expect(result.endsWith('```')).toBe(true)
    })

    it('应该闭合未完成的行内代码', () => {
      const input = '这是 `代码'
      const result = processLatexInMarkdown(input, true)
      expect(result.endsWith('`')).toBe(true)
    })

    it('应该闭合未完成的数学公式', () => {
      const input = '公式：$$x^2'
      const result = processLatexInMarkdown(input, true)
      expect(result.endsWith('$$')).toBe(true)
    })

    it('不应该闭合已完成的公式', () => {
      const input = '$$x^2$$'
      const result = processLatexInMarkdown(input, true)
      expect(result).toBe('$$x^2$$')
    })
  })

  describe('复杂场景', () => {
    it('应该正确处理混合内容', () => {
      const input = '反应式：\\text{Cu} + 2\\text{H}_2\\text{SO}_4\n这是说明'
      const result = processLatexInMarkdown(input)
      expect(result).toContain('$$\\text{Cu} + 2\\text{H}_2\\text{SO}_4$$')
      expect(result).toContain('这是说明')
    })

    it('应该处理多个公式在同一行', () => {
      const input = 'x^2 和 y^2'
      const result = processLatexInMarkdown(input)
      const mathBlocks = result.match(/\$\$/g)
      expect(mathBlocks).toHaveLength(4) // 2个公式，每个有2个$$
    })
  })
})
