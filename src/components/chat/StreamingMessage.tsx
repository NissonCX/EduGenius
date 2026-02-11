                <div className="p-6 markdown-content">
                  <ReactMarkdown
                      // Mermaid 图表
                      code(props: any) {
                        const { node, inline, className, children, ...rest } = props
                        const match = /language-mermaid/.exec(className || '')
                        if (!inline && match) {
                          const code = String(children).replace(/\n$/, '')
                          return <MermaidInText text={`\`\`\`mermaid\n${code}\n\`\`\``} />
                        }

                        // 代码块
                        if (!inline) {
                          return (
                            <div className="my-5">
                              <div className="bg-gray-900 rounded-xl overflow-hidden shadow-lg border border-gray-800">
                                <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
                                  <span className="text-xs font-medium text-gray-300 font-mono">
                                    {className?.replace('language-', '') || 'code'}
                                  </span>
