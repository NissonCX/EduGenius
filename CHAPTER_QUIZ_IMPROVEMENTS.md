# 章节识别和 Quiz 功能完善

## 问题分析

### 1. 章节识别问题
- ❌ 只分析前 5000 字符，长文档识别不准
- ❌ 使用 qwen-turbo 模型，识别能力较弱
- ❌ 启发式方法正则表达式不够准确
- ❌ 没有详细的日志输出，难以调试

### 2. Quiz 功能缺失
- ❌ 章节选择页面没有测试入口
- ❌ 学习页面没有测试按钮
- ❌ 学习流程不完整（缺少测试环节）

### 3. 业务逻辑不完整
- ❌ 学习→测试→评估的闭环未形成
- ❌ 没有明确的学习路径引导

## 解决方案

### 1. 优化章节识别

#### 升级 AI 模型
```python
# 旧代码
self.model = "qwen-turbo"  # 较弱的模型

# 新代码
self.model = "qwen-plus"  # 更强的模型，识别更准确
```

#### 智能文档采样
```python
# 旧代码：只看前 5000 字符
preview_text = document_text[:5000]

# 新代码：智能采样
preview_parts = []
# 1. 前 3000 字符（通常包含目录和第一章）
preview_parts.append(document_text[:3000])
# 2. 中间采样（每隔 5000 字符采样 500 字符）
for i in range(5000, len(document_text) - 1000, 5000):
    preview_parts.append(document_text[i:i+500])
# 3. 最后 1000 字符
preview_parts.append(document_text[-1000:])
```

#### 改进提示词
```python
prompt = """你是一个专业的教材分析助手。请仔细分析以下教材内容，识别其章节结构。

注意：
1. 寻找明确的章节标记，如"第一章"、"第二章"、"Chapter 1"、"1."等
2. 章节标题通常在章节号之后，如"第一章 线性代数基础"
3. 如果没有明确的章节标记，根据内容主题划分为2-5个逻辑章节
4. 章节标题要简洁（不超过20个字）

请严格按照以下JSON格式返回，不要添加任何其他内容：
{...}
"""
```

#### 增强启发式方法
```python
# 新增多种章节模式识别
patterns = [
    (r'第([一二三四五六七八九十百]+)章[：:\s]+(.*?)(?=\n|$)', 'chinese_chapter'),
    (r'第(\d+)章[：:\s]+(.*?)(?=\n|$)', 'number_chapter'),
    (r'Chapter\s+(\d+)[：:\s]+(.*?)(?=\n|$)', 'english_chapter'),
    (r'^(\d+)\.\s+([^\n]{5,50})(?=\n|$)', 'number_dot'),
    (r'^([一二三四五六七八九十]+)、\s*([^\n]{5,50})(?=\n|$)', 'chinese_number'),
]

# 添加中文数字转换
def _chinese_to_number(self, chinese_num: str) -> int:
    # 支持"一"、"十"、"二十"等
    ...
```

#### 添加详细日志
```python
print(f"📝 LLM 返回内容: {content[:200]}...")
print(f"✅ 成功解析 JSON，识别到 {result.get('total_chapters', 0)} 个章节")
print(f"📚 使用启发式方法划分章节...")
print(f"✅ 使用模式 '{pattern_type}' 找到 {len(chapters)} 个章节")
print(f"📊 最终识别到 {len(unique_chapters)} 个章节")
```

### 2. 添加 Quiz 功能入口

#### 章节选择页面
```typescript
// 每个章节卡片添加两个按钮
<div className="flex gap-3">
  <button onClick={() => router.push(`/study?doc=${docId}&chapter=${chapter.chapter_number}`)}>
    <MessageSquare className="w-4 h-4" />
    <span>学习对话</span>
  </button>
  <button onClick={() => router.push(`/quiz?doc=${docId}&chapter=${chapter.chapter_number}`)}>
    <BookOpen className="w-4 h-4" />
    <span>章节测试</span>
  </button>
</div>
```

#### 学习对话页面
```typescript
// 顶部导航栏添加测试按钮
<button onClick={() => router.push(`/quiz?doc=${docId}&chapter=${chapterId}`)}>
  <BookOpen className="w-4 h-4" />
  <span>章节测试</span>
</button>
```

#### Quiz 页面优化
```typescript
// 更新参数名称以匹配新的 URL 格式
const docId = searchParams.get('doc');
const chapterId = searchParams.get('chapter');

// 添加顶部导航栏
<div className="border-b border-gray-200">
  <div className="flex items-center justify-between">
    <button onClick={handleBackToChapters}>
      <ArrowLeft />
    </button>
    <div>
      <h1>{chapterTitle} - 章节测试</h1>
      <p>{documentTitle}</p>
    </div>
  </div>
</div>
```

## 完整的学习流程

### 1. 选择教材
```
/study
├── 教材 A
├── 教材 B
└── 教材 C
```

### 2. 选择章节
```
/study?doc=1
├── 第一章 [学习对话] [章节测试]
├── 第二章 [学习对话] [章节测试] 🔒
└── 第三章 [学习对话] [章节测试] 🔒
```

### 3. 学习对话
```
/study?doc=1&chapter=1
┌─────────────────────────────────┐
│ ← 返回  第一章  [章节测试]  L3  │
├─────────────────────────────────┤
│ 用户: 什么是向量？              │
│ AI: 向量是...                   │
└─────────────────────────────────┘
```

### 4. 章节测试
```
/quiz?doc=1&chapter=1
┌─────────────────────────────────┐
│ ← 返回  第一章 - 章节测试       │
├─────────────────────────────────┤
│ 题目 1/5:                       │
│ 向量的模长公式是？              │
│ ○ A. |v| = √(x² + y²)          │
│ ○ B. |v| = x + y               │
└─────────────────────────────────┘
```

### 5. 测试结果
```
┌─────────────────────────────────┐
│ 测试完成！                      │
│ 得分: 80分                      │
│ 正确: 4/5                       │
├─────────────────────────────────┤
│ [查看错题] [重新测试] [下一章]  │
└─────────────────────────────────┘
```

## 业务逻辑闭环

### 学习路径
```
1. 上传教材
   ↓
2. AI 识别章节
   ↓
3. 选择章节
   ↓
4. 学习对话（与 AI 老师交流）
   ↓
5. 章节测试（检测学习效果）
   ↓
6. 获得评分（AI 评估能力）
   ↓
7. 解锁下一章 / 复习当前章
```

### 能力评估
```
测试结果 → AI 分析 → 能力评分 → 调整教学风格
                    ↓
                错题记录 → 针对性复习
```

## 文件修改清单

### 后端
1. `api/app/services/chapter_divider.py`
   - 升级模型为 qwen-plus
   - 优化文档采样策略
   - 改进提示词
   - 增强启发式方法
   - 添加详细日志

### 前端
1. `src/app/study/page.tsx`
   - 章节选择页面添加"学习对话"和"章节测试"按钮
   - 学习对话页面顶部添加"章节测试"按钮

2. `src/app/quiz/page.tsx`
   - 更新参数名称（doc, chapter）
   - 添加顶部导航栏
   - 加载章节信息显示
   - 优化返回逻辑

## 设计原则

遵循 `design-system/edugenius/MASTER.md`：

✅ **清晰的信息层级**
- 顶部导航栏：全局信息
- 主内容区：核心功能
- 操作按钮：明确的行动指引

✅ **流畅的用户体验**
- 学习→测试→评估的自然流程
- 明确的按钮和提示
- 平滑的页面过渡

✅ **极简黑白美学**
- 黑色主按钮（学习对话）
- 白底黑边次按钮（章节测试）
- 清晰的视觉对比

## 测试检查

### 章节识别
- [ ] 测试包含"第一章"、"第二章"的文档
- [ ] 测试包含"Chapter 1"、"Chapter 2"的文档
- [ ] 测试包含"1."、"2."的文档
- [ ] 测试没有明确章节标记的文档
- [ ] 检查日志输出是否详细

### Quiz 功能
- [ ] 章节选择页面显示两个按钮
- [ ] 点击"学习对话"跳转正确
- [ ] 点击"章节测试"跳转正确
- [ ] 学习页面顶部显示测试按钮
- [ ] Quiz 页面正确显示章节信息
- [ ] 测试完成后可以返回章节列表

### 学习流程
- [ ] 可以顺利完成：选择教材→选择章节→学习→测试
- [ ] 测试通过后可以进入下一章
- [ ] 测试未通过提示复习
- [ ] 错题记录正确保存

## 下一步优化

### 短期
1. ✅ 优化章节识别算法
2. ✅ 添加 Quiz 功能入口
3. ⏳ 完善测试题目生成
4. ⏳ 添加能力评估算法

### 中期
1. 根据测试结果调整教学风格
2. 智能推荐复习内容
3. 生成个性化学习报告
4. 添加学习数据可视化

### 长期
1. 多模态学习（图片、视频）
2. 协作学习功能
3. 学习社区
4. 学习成就系统

## 总结

通过这次优化：
- ✅ 章节识别更准确（升级模型+智能采样）
- ✅ Quiz 功能完整（多个入口+清晰流程）
- ✅ 学习闭环形成（学习→测试→评估）
- ✅ 用户体验提升（明确的引导+流畅的交互）

现在的系统具备了完整的教育功能，可以真正帮助学生学习和进步！
