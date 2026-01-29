# 性能优化和小节支持

## 问题分析

### 1. 内存泄漏问题

#### 发现的问题
1. **useEffect 缺少清理函数**
   - 组件卸载后仍在更新状态
   - 事件监听器未移除
   - setTimeout/setInterval 未清理

2. **依赖项不完整**
   - useEffect 依赖项缺失
   - 导致不必要的重新渲染

3. **大量动画组件**
   - framer-motion 动画未优化
   - AnimatePresence 使用过多

#### 具体位置
```typescript
// ❌ 问题代码
useEffect(() => {
  loadData()
}, [user.id, chapterId, chapterTitle]) // 缺少 cleanup

// ❌ 问题代码
setTimeout(() => {
  setUploadStatus('idle')
}, 3000) // 组件卸载后仍执行

// ❌ 问题代码
window.addEventListener('resize', checkMobile) // 未移除监听器
```

### 2. 小节支持缺失

#### 当前问题
- ❌ 只有章节，没有小节
- ❌ 用户无法按小节学习
- ❌ 进度追踪不够细粒度

#### 需求
- ✅ 章节下有多个小节
- ✅ 用户按小节学习
- ✅ 小节级别的进度追踪
- ✅ 小节级别的测试

## 解决方案

### 1. 性能优化

#### A. 修复内存泄漏

##### StudyChat.tsx
```typescript
useEffect(() => {
  let isMounted = true // 防止组件卸载后更新状态
  let abortController = new AbortController() // 取消请求

  const loadHistory = async () => {
    try {
      const response = await fetch(url, {
        signal: abortController.signal
      })
      
      if (response.ok && isMounted) {
        setMessages(data)
      }
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error(error)
      }
    }
  }

  loadHistory()

  return () => {
    isMounted = false
    abortController.abort() // 取消请求
  }
}, [user.id, chapterId])
```

##### Sidebar.tsx
```typescript
useEffect(() => {
  const handleResize = () => setIsMobile(window.innerWidth < 768)
  
  window.addEventListener('resize', handleResize)
  
  return () => {
    window.removeEventListener('resize', handleResize) // 清理
  }
}, [])
```

##### Documents.tsx
```typescript
useEffect(() => {
  let timeoutId: NodeJS.Timeout

  if (uploadStatus === 'success') {
    timeoutId = setTimeout(() => {
      setUploadStatus('idle')
    }, 3000)
  }

  return () => {
    if (timeoutId) {
      clearTimeout(timeoutId) // 清理
    }
  }
}, [uploadStatus])
```

#### B. 优化渲染性能

##### 使用 React.memo
```typescript
// 避免不必要的重新渲染
export const ChatMessage = React.memo(({ message }: ChatMessageProps) => {
  // ...
})

export const ChapterCard = React.memo(({ chapter }: ChapterCardProps) => {
  // ...
})
```

##### 使用 useMemo 和 useCallback
```typescript
// 缓存计算结果
const filteredChapters = useMemo(() => {
  return chapters.filter(ch => !ch.is_locked)
}, [chapters])

// 缓存回调函数
const handleChapterClick = useCallback((chapterId: number) => {
  router.push(`/study?doc=${docId}&chapter=${chapterId}`)
}, [docId, router])
```

##### 懒加载组件
```typescript
// 延迟加载大型组件
const Quiz = lazy(() => import('@/components/quiz/Quiz'))
const MermaidDiagram = lazy(() => import('@/components/visualization/MermaidDiagram'))

<Suspense fallback={<Loader />}>
  <Quiz />
</Suspense>
```

#### C. 减少动画开销

```typescript
// 使用 CSS 动画替代 framer-motion（简单动画）
<div className="transition-all duration-200 hover:scale-105">
  {/* 内容 */}
</div>

// 只在必要时使用 framer-motion
<motion.div
  initial={false} // 禁用初始动画
  animate={{ opacity: 1 }}
  transition={{ duration: 0.2 }} // 缩短动画时间
>
  {/* 内容 */}
</motion.div>
```

### 2. 小节支持

#### A. 数据库模型

##### 添加 Subsection 表
```sql
CREATE TABLE subsections (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL,
    chapter_number INTEGER NOT NULL,
    subsection_number INTEGER NOT NULL,
    subsection_title VARCHAR(500),
    content_summary TEXT,
    estimated_time_minutes INTEGER DEFAULT 15,
    FOREIGN KEY (document_id) REFERENCES documents(id),
    UNIQUE (document_id, chapter_number, subsection_number)
);
```

##### 更新 Progress 表
```sql
ALTER TABLE progress ADD COLUMN subsection_number INTEGER DEFAULT NULL;
ALTER TABLE progress ADD COLUMN subsection_progress FLOAT DEFAULT 0.0;
```

#### B. 后端 API

##### 章节划分服务
```python
class ChapterDivider:
    async def extract_table_of_contents(self, document_text, document_title):
        """提取目录，包括章节和小节"""
        
        prompt = """
        请提取目录结构，包括章节和小节：
        
        {
            "chapters": [
                {
                    "chapter_number": 1,
                    "chapter_title": "线性代数基础",
                    "subsections": [
                        {"subsection_number": 1, "subsection_title": "向量的定义"},
                        {"subsection_number": 2, "subsection_title": "向量的运算"}
                    ]
                }
            ]
        }
        """
```

##### API 端点
```python
@router.get("/api/documents/{doc_id}/chapters/{chapter_num}/subsections")
async def get_subsections(doc_id: int, chapter_num: int):
    """获取章节的所有小节"""
    return {
        "chapter_number": chapter_num,
        "subsections": [
            {
                "subsection_number": 1,
                "subsection_title": "向量的定义",
                "is_completed": True,
                "progress": 100
            },
            {
                "subsection_number": 2,
                "subsection_title": "向量的运算",
                "is_completed": False,
                "progress": 30
            }
        ]
    }
```

#### C. 前端界面

##### 章节详情页（显示小节列表）
```typescript
// /study?doc=1&chapter=1
<div>
  <h2>第一章：线性代数基础</h2>
  
  <div className="subsections">
    {subsections.map(sub => (
      <SubsectionCard
        key={sub.subsection_number}
        subsection={sub}
        onClick={() => router.push(
          `/study?doc=${docId}&chapter=${chapterId}&section=${sub.subsection_number}`
        )}
      />
    ))}
  </div>
</div>
```

##### 小节学习页
```typescript
// /study?doc=1&chapter=1&section=1
<div>
  <nav>
    ← 返回章节  |  1.1 向量的定义  |  [上一节] [下一节]
  </nav>
  
  <StudyChat
    documentId={docId}
    chapterNumber={chapterId}
    subsectionNumber={sectionId}
  />
</div>
```

##### 小节卡片组件
```typescript
interface SubsectionCardProps {
  subsection: {
    subsection_number: number
    subsection_title: string
    is_completed: boolean
    progress: number
    estimated_time: number
  }
  onClick: () => void
}

export function SubsectionCard({ subsection, onClick }: SubsectionCardProps) {
  return (
    <motion.button
      onClick={onClick}
      className="p-4 border rounded-xl hover:border-black"
    >
      <div className="flex items-center gap-3">
        {/* 完成状态图标 */}
        {subsection.is_completed ? (
          <CheckCircle2 className="w-5 h-5 text-green-600" />
        ) : (
          <Circle className="w-5 h-5 text-gray-400" />
        )}
        
        {/* 小节信息 */}
        <div className="flex-1 text-left">
          <h4 className="font-medium">
            {subsection.subsection_number}. {subsection.subsection_title}
          </h4>
          <p className="text-sm text-gray-500">
            预计 {subsection.estimated_time} 分钟
          </p>
        </div>
        
        {/* 进度 */}
        <div className="text-sm text-gray-600">
          {subsection.progress}%
        </div>
      </div>
      
      {/* 进度条 */}
      {subsection.progress > 0 && (
        <div className="mt-2 h-1 bg-gray-100 rounded-full">
          <div 
            className="h-full bg-black rounded-full"
            style={{ width: `${subsection.progress}%` }}
          />
        </div>
      )}
    </motion.button>
  )
}
```

## 新的学习流程

### 1. 选择教材
```
/study
└── 教材列表
```

### 2. 选择章节
```
/study?doc=1
├── 第一章：线性代数基础
├── 第二章：矩阵理论
└── 第三章：微积分入门
```

### 3. 选择小节
```
/study?doc=1&chapter=1
├── 1.1 向量的定义 ✓
├── 1.2 向量的运算 (30%)
├── 1.3 向量空间
└── 1.4 线性相关性
```

### 4. 学习小节
```
/study?doc=1&chapter=1&section=1
┌─────────────────────────────────┐
│ ← 返回  1.1 向量的定义  [下一节]│
├─────────────────────────────────┤
│ AI 对话界面                     │
└─────────────────────────────────┘
```

### 5. 小节测试
```
/quiz?doc=1&chapter=1&section=1
└── 1.1 向量的定义 - 小节测试
```

## 性能优化清单

### 内存泄漏修复
- [ ] StudyChat.tsx - 添加 cleanup 函数
- [ ] Sidebar.tsx - 移除事件监听器
- [ ] Documents.tsx - 清理 setTimeout
- [ ] MobileNav.tsx - 清理 resize 监听器
- [ ] StrictnessMenu.tsx - 清理 click 监听器
- [ ] KnowledgeConstellation.tsx - 清理 resize 监听器

### 渲染优化
- [ ] 使用 React.memo 包装组件
- [ ] 使用 useMemo 缓存计算
- [ ] 使用 useCallback 缓存回调
- [ ] 懒加载大型组件
- [ ] 虚拟滚动长列表

### 动画优化
- [ ] 简单动画使用 CSS
- [ ] 减少 framer-motion 使用
- [ ] 缩短动画时间
- [ ] 禁用不必要的初始动画

### 网络优化
- [ ] 使用 AbortController 取消请求
- [ ] 添加请求缓存
- [ ] 防抖和节流
- [ ] 分页加载数据

## 实施计划

### 第一阶段：性能优化（紧急）
1. 修复所有内存泄漏
2. 添加 React.memo
3. 优化动画

### 第二阶段：小节支持（重要）
1. 更新数据库模型
2. 实现后端 API
3. 更新前端界面

### 第三阶段：测试和优化
1. 性能测试
2. 内存泄漏检测
3. 用户体验优化

## 预期效果

### 性能提升
- ✅ 内存使用减少 50%
- ✅ 页面加载速度提升 30%
- ✅ 动画更流畅
- ✅ 无内存泄漏

### 功能增强
- ✅ 支持小节学习
- ✅ 更细粒度的进度追踪
- ✅ 更好的学习体验
- ✅ 更灵活的学习路径

## 总结

通过这次优化：
1. **解决内存泄漏** - 添加清理函数，移除监听器
2. **优化渲染性能** - 使用 memo、useMemo、useCallback
3. **支持小节学习** - 更细粒度的学习单元
4. **提升用户体验** - 更快、更流畅、更灵活

这将使系统更加稳定、高效、易用！
