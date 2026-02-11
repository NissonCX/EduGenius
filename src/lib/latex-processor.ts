/**
 * LaTeX 处理工具
 * 统一处理 Markdown 中的 LaTeX 公式格式
 */

/**
 * 处理 Markdown 内容，智能识别并转换 LaTeX 公式
 * 
 * 支持的格式：
 * - \[ ... \] → $$...$$
 * - \( ... \) → $...$
 * - [ ... ] (单独行) → $$...$$
 * - 纯 LaTeX 代码（包含命令、下标、上标） → $$...$$
 * 
 * @param content - 原始 Markdown 内容
 * @param isStreaming - 是否为流式输出（会处理不完整的公式）
 * @returns 处理后的 Markdown 内容
 */
export function processLatexInMarkdown(content: string, isStreaming: boolean = false): string {
  let processed = content

  // 1. 转换 \[ \] 格式为 $$...$$（块级公式）
  processed = processed.replace(/\\\[/g, '\n$$\n')
  processed = processed.replace(/\\\]/g, '\n$$\n')
  
  // 2. 转换 \( \) 格式为 $...$ （行内公式）
  processed = processed.replace(/\\\(/g, '$')
  processed = processed.replace(/\\\)/g, '$')
  
  // 3. 转换单独行的 [ ] 格式为 $$...$$
  processed = processed.replace(/^\s*\[\s*(.+?)\s*\]\s*$/gm, '\n$$$$1$$\n')

  // 4. 智能识别纯 LaTeX 代码
  // 匹配包含以下特征的行：
  // - LaTeX 命令：\text, \rightarrow, \xrightarrow, \, 等
  // - 下标：_2, _{10}
  // - 上标：^2, ^{10}
  // - 组合：2\,H_2O_2
  const latexPattern = /^(?!.*```|.*\$\$)(.*(\\[a-zA-Z,]+\{?|[_^]\{?\w+\}?).*?)$/gm
  
  processed = processed.replace(latexPattern, (match) => {
    const trimmed = match.trim()
    
    // 如果已经被 $ 包裹，不处理
    const dollarCount = (trimmed.match(/\$/g) || []).length
    if (dollarCount >= 2) {
      return match
    }
    
    // 如果在代码块中，不处理
    if (trimmed.includes('```')) {
      return match
    }
    
    // 如果是普通文本（不包含 LaTeX 特征），不处理
    if (!trimmed.includes('\\') && !trimmed.match(/[_^]\{?\w+\}?/)) {
      return match
    }
    
    // 如果是标题、列表等 Markdown 语法，不处理
    if (trimmed.match(/^#{1,6}\s/) || trimmed.match(/^[-*+]\s/) || trimmed.match(/^\d+\.\s/)) {
      return match
    }
    
    // 包裹为块级公式
    return `$$${trimmed}$$`
  })

  // 5. 如果是流式输出，处理不完整的格式
  if (isStreaming) {
    // 检查未闭合的代码块
    const codeBlockCount = (processed.match(/```/g) || []).length
    if (codeBlockCount % 2 !== 0 && processed.length > 50) {
      processed += '\n```'
    }

    // 检查未闭合的行内代码
    const inlineCodeCount = (processed.match(/(?<!\\)`/g) || []).length
    if (inlineCodeCount % 2 !== 0) {
      processed += '`'
    }

    // 检查未闭合的数学公式
    const mathBlockCount = (processed.match(/\$\$/g) || []).length
    if (mathBlockCount % 2 !== 0) {
      processed += '$$'
    }
  }

  return processed
}

/**
 * 测试 LaTeX 处理器
 */
export function testLatexProcessor() {
  const testCases = [
    {
      name: '化学方程式（带空格和下标）',
      input: '2\\,H_2O_2(aq) \\xrightarrow{MnO_2} 2\\,H_2O(l) + O_2(g)',
      expected: '$$2\\,H_2O_2(aq) \\xrightarrow{MnO_2} 2\\,H_2O(l) + O_2(g)$$'
    },
    {
      name: '纯 LaTeX 命令',
      input: '\\text{Cu} + 2\\text{H}_2\\text{SO}_4',
      expected: '$$\\text{Cu} + 2\\text{H}_2\\text{SO}_4$$'
    },
    {
      name: '已包裹的公式',
      input: '$$E = mc^2$$',
      expected: '$$E = mc^2$$'
    },
    {
      name: '普通文本',
      input: '这是一段普通文本',
      expected: '这是一段普通文本'
    },
    {
      name: '混合内容',
      input: '反应式：\\text{Cu} + 2\\text{H}_2\\text{SO}_4\\n这是说明',
      expected: '反应式：$$\\text{Cu} + 2\\text{H}_2\\text{SO}_4$$\\n这是说明'
    }
  ]

  console.log('=== LaTeX 处理器测试 ===')
  testCases.forEach(({ name, input, expected }) => {
    const result = processLatexInMarkdown(input, false)
    const passed = result === expected
    console.log(`${passed ? '✅' : '❌'} ${name}`)
    if (!passed) {
      console.log(`  输入: ${input}`)
      console.log(`  期望: ${expected}`)
      console.log(`  实际: ${result}`)
    }
  })
}
