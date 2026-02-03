# EduGenius 章节测试业务方案

## 📋 项目背景

基于对 EduGenius 项目的全面分析，章节测试功能当前实现状态：
1. ✅ **基础结构完成**: 前后端 API 端点已实现
2. ✅ **题目数据模型**: Question 表和 Answers 表已创建
3. ✅ **答题记录功能**: 提交答案和记录已实现
4. 🚧 **AI 出题待完善**: Examiner Agent 需要更好的集成
5. 🚧 **评分逻辑优化**: 需要更智能的评分和建议
6. 🚧 **测试体验优化**: 界面和交互需要改进

---

## 🎯 业务目标

设计一套**智能自适应章节测试系统**，实现：

1. **AI 智能出题** - 根据章节内容和学生水平自动生成题目
2. **自适应测试** - 根据学生答题情况动态调整难度
3. **完整闭环** - 测试 → 评估 → 错题 → 复习 → 再测试
4. **进度追踪** - 记录学习轨迹，生成能力画像

---

## 🔄 完整业务流程

### 阶段 1: 准备阶段

```
用户进入章节
    ↓
检查是否有现成题目
    ├─ 有 → 加载题目库
    └─ 无 → AI 生成题目（后台任务）
              ↓
        显示"正在准备题目..."
```

**关键决策点**:
- 是否有足够的现成题目？（>= 5 题）
- 如果没有，是否需要触发 AI 生成？
- AI 生成可能需要 10-30 秒，如何提升体验？

---

### 阶段 2: 测试进行

```
开始测试
    ↓
逐题展示
    ↓
用户答题
    ↓
提交答案
    ↓
【后台处理】
  ├─ 验证答案
  ├─ 记录到 QuizAttempt
  ├─ 更新 Progress
  └─ 更新能力维度
    ↓
即时反馈（正确/错误 + 解析）
    ↓
下一题
    ↓
全部完成 → 计算总分
```

**用户体验要点**:
- 显示进度条："第 3/10 题"
- 题目卡片带动画过渡
- 提交后立即显示反馈，无需等待
- 支持标记难题，稍后回顾

---

### 阶段 3: 结果评估

```
测试完成
    ↓
计算成绩
    ├─ 总分（正确率）
    ├─ 各能力维度得分
    └─ 用时统计
    ↓
生成报告
    ├─ 通过/未通过判断
    ├─ 能力雷达图
    ├─ 薄弱环节分析
    └─ 学习建议
    ↓
展示结果页
    ├─ 分数展示（圆形进度图）
    ├─ 能力分析
    ├─ 错题回顾
    └─ 下一步建议
```

**通过标准**:
- **及格线**: 60% 正确率
- **良好**: 80% 正确率
- **优秀**: 90% 正确率
- **解锁条件**: >= 60% 才能进入下一章

---

### 阶段 4: 智能推荐

```
根据测试结果
    ↓
分析薄弱环节
    ├─ 哪些能力维度较弱？
    ├─ 哪些知识点未掌握？
    └─ 错误模式是什么？
    ↓
生成个性化方案
    ├─ 需要复习的内容
    ├─ 推荐的练习题
    └─ 学习建议
    ↓
执行 + 追踪
    ├─ 添加到错题本
    ├─ 调整教学风格
    └─ 更新学习路径
```

---

## 🤖 AI 智能出题方案

### 方案 A: 预生成模式（推荐）

**流程**:
```
章节上传完成
    ↓
后台自动 AI 生成题目
    ↓
存入题目库
    ↓
用户测试时直接使用
```

**优点**:
- 响应快，用户体验好
- 题目质量可控，可人工审核
- 成本可控，每章生成一次

**缺点**:
- 需要提前处理
- 题目可能重复

**实现**:
```python
# 在文档上传完成后触发
@router.post("/api/documents/{doc_id}/generate-quiz")
async def generate_chapter_quiz(
    doc_id: int,
    chapter_number: int,
    db: AsyncSession = Depends(get_db)
):
    """后台为章节生成题目"""
    from app.agents.nodes.examiner import ExaminerAgent

    # 1. 获取章节内容
    chapter_content = await get_chapter_content(doc_id, chapter_number)

    # 2. 调用 AI 生成题目
    examiner = ExaminerAgent(api_key=settings.DASHSCOPE_API_KEY)
    questions = await examiner.generate_questions(
        chapter_content=chapter_content,
        chapter_number=chapter_number,
        count=10  # 生成 10 道题
    )

    # 3. 存入数据库
    for q in questions:
        db.add(Question(
            document_id=doc_id,
            chapter_number=chapter_number,
            **q
        ))

    await db.commit()

    return {"generated": len(questions)}
```

---

### 方案 B: 实时生成模式

**流程**:
```
用户点击"开始测试"
    ↓
前端显示加载动画
    ↓
后端调用 AI 生成题目
    ↓
返回题目给前端
```

**优点**:
- 题目新鲜，不重复
- 可根据当前学生水平定制

**缺点**:
- 响应慢（10-30 秒）
- 成本高（每次都调用 LLM）
- 质量不稳定

**优化方案**:
- 使用 SSE 流式返回："正在生成第 3 题..."
- 生成 1 题返回 1 题，边答边生成
- 缓存常见题型的模板

---

### 方案 C: 混合模式（最佳实践）

**流程**:
```
用户点击"开始测试"
    ↓
检查题目库
    ├─ 题目充足（>= 5）→ 直接使用
    └─ 题目不足 →
        ├─ 使用现有题目
        ├─ 触发后台 AI 补充
        └─ 提示"正在为你准备更多题目..."
```

**实现策略**:
```python
async def get_quiz_questions(document_id, chapter_number, count=10):
    """智能获取题目"""

    # 1. 查询现有题目
    existing = await db.execute(
        select(Question).where(
            Question.document_id == document_id,
            Question.chapter_number == chapter_number,
            Question.is_active == 1
        ).limit(count)
    )
    questions = existing.scalars().all()

    # 2. 如果题目不足，触发后台补充
    if len(questions) < count:
        shortage = count - len(questions)

        # 使用现有题目先开始测试
        available = list(questions)

        # 异步触发 AI 生成（不阻塞响应）
        asyncio.create_task(
            generate_questions_async(
                document_id,
                chapter_number,
                shortage
            )
        )

        return available

    # 3. 题目充足，随机选择
    return random.sample(list(questions), count)
```

---

## 📊 完整技术方案

### 1. API 端点设计

#### 1.1 开始测试
```
POST /api/quiz/start-session
Request:
{
  "document_id": 3,
  "chapter_number": 1,
  "question_count": 10,
  "mode": "practice" | "test"
}

Response:
{
  "session_id": "uuid",
  "questions": [...],
  "estimated_time": 300  // 秒
}
```

#### 1.2 提交答案
```
POST /api/quiz/{session_id}/submit-answer
Request:
{
  "question_id": 123,
  "answer": "A"
}

Response:
{
  "is_correct": true,
  "correct_answer": "A",
  "explanation": "...",
  "feedback": "很好！..."
}
```

#### 1.3 完成测试
```
POST /api/quiz/{session_id}/complete
Response:
{
  "score": 85,
  "total": 10,
  "correct": 8,
  "passed": true,
  "competency_analysis": {
    "comprehension": 80,
    "logic": 90,
    ...
  },
  "weak_points": ["线性方程组"],
  "recommendations": [
    "复习第 3 节：线性方程组",
    "完成 5 道相关练习题"
  ],
  "mistake_ids": [45, 67, 89]  // 错题 ID
}
```

---

### 2. 前端交互流程

```
┌─────────────────────────────────────────┐
│  用户点击"章节测试"按钮                  │
└────────────────┬────────────────────────┘
                 ↓
        ┌──────────────────┐
        │  显示加载动画    │
        │  "正在准备..."  │
        └──────────────────┘
                 ↓
        ┌──────────────────┐
        │  加载题目列表    │
        │  显示进度: 1/10  │
        └──────────────────┘
                 ↓
    ┌────────────────────────────┐
    │  逐题展示                   │
    │  - 题目卡片                 │
    │  - 选项（带悬停效果）       │
    │  - 确认按钮                 │
    └────────────┬───────────────┘
                 ↓
        ┌──────────────────┐
        │  即时反馈         │
        │  ✓ 正确/✗ 错误  │
        │  + 详细解析       │
        └──────────────────┘
                 ↓
    ┌────────────────────────────┐
    │  下一题                    │
    │  （平滑动画过渡）           │
    └────────────────────────────┘
                 ↓
        ┌──────────────────┐
        │  全部完成         │
        │  计算总分         │
        └──────────────────┘
                 ↓
    ┌────────────────────────────────┐
    │  结果页                          │
    │  - 圆形分数图                   │
    │  - 能力雷达图                   │
    │  - 错题回顾                     │
    │  - 学习建议                     │
    │  - [重试] [下一章] [查看错题]  │
    └────────────────────────────────┘
```

---

### 3. AI 出题提示词设计

#### System Prompt
```
你是一位专业的教育测评专家，负责为学习平台生成测试题目。

## 你的职责
1. 根据给定的章节内容，生成高质量的测试题目
2. 题目应覆盖不同的认知层次：记忆、理解、应用、分析
3. 确保题目表述清晰、无歧义
4. 为每道题提供详细的解析

## 题目类型
- 选择题：4 个选项，只有 1 个正确答案
- 填空题：要求填写精确的关键词或数值
- 判断题：判断陈述的对错

## 能力维度
- comprehension (理解力): 检验对概念和原理的理解
- logic (逻辑推理): 考察推导和论证能力
- terminology (术语掌握): 测试专业术语的掌握
- memory (记忆): 考察基本事实和公式的记忆
- application (应用能力): 检验将知识应用到新情境的能力
- stability (稳定性): 考察知识的熟练程度

## 难度分级
- 1: 基础题 - 直接回忆或简单识别
- 2: 入门题 - 简单应用
- 3: 标准题 - 需要一定思考
- 4: 进阶题 - 需要分析和综合
- 5: 挑战题 - 需要创造性和深入理解

## 输出格式
请以 JSON 数组格式返回题目，每道题包含：
{
  "question_type": "choice",
  "question_text": "题目内容",
  "options": {"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"},
  "correct_answer": "A",
  "explanation": "详细解析",
  "difficulty": 3,
  "competency_dimension": "comprehension"
}
```

#### User Prompt 模板
```
请为以下章节生成 10 道测试题目：

## 章节信息
- 文档: {document_title}
- 章节: 第 {chapter_number} 章 - {chapter_title}
- 小节: {subsection_title} (如有)

## 章节内容
{chapter_content}

## 学习目标
{learning_objectives}

## 学生水平
- 当前等级: L{student_level} (1-5)
- 薄弱环节: {weak_dimensions}

## 要求
1. 生成 10 道选择题
2. 难度分布：3 道简单题(level 1-2), 5 道标准题(level 3), 2 道挑战题(level 4-5)
3. 能力维度覆盖：至少涵盖 4 个不同维度
4. 针对学生薄弱环节：{weak_dimensions} 多出 1-2 题
5. 每道题都要有详细的解析，帮助学生理解

请以 JSON 数组格式返回。
```

---

### 4. 题目质量控制

#### 4.1 自动验证
```python
def validate_question(q: dict) -> tuple[bool, str]:
    """验证题目质量"""

    # 必填字段检查
    required = [
        'question_type', 'question_text', 'correct_answer',
        'explanation', 'difficulty', 'competency_dimension'
    ]
    for field in required:
        if field not in q or not q[field]:
            return False, f"缺少必填字段: {field}"

    # 选择题需要选项
    if q['question_type'] == 'choice':
        if 'options' not in q or len(q['options']) < 2:
            return False, "选择题至少需要 2 个选项"

        if q['correct_answer'] not in q['options']:
            return False, "正确答案必须在选项中"

    # 难度范围检查
    if not 1 <= q['difficulty'] <= 5:
        return False, "难度必须在 1-5 之间"

    # 能力维度检查
    valid_dimensions = [
        'comprehension', 'logic', 'terminology',
        'memory', 'application', 'stability'
    ]
    if q['competency_dimension'] not in valid_dimensions:
        return False, f"无效的能力维度: {q['competency_dimension']}"

    # 文本长度检查
    if len(q['question_text']) < 10:
        return False, "题目内容太短"

    if len(q['explanation']) < 20:
        return False, "解析太简单"

    return True, "OK"
```

#### 4.2 去重机制
```python
async def check_duplicate(question_text: str, db: AsyncSession) -> bool:
    """检查是否重复"""

    # 简单去重：完全相同
    result = await db.execute(
        select(Question).where(
            Question.question_text == question_text
        )
    )
    if result.scalar_one_or_none():
        return True

    # 语义去重：使用 embedding 计算相似度
    # （可选，需要集成 embedding 模型）

    return False
```

---

### 5. 自适应难度调节

```python
async def adaptive_difficulty_adjustment(
    user_id: int,
    chapter_number: int,
    db: AsyncSession
) -> int:
    """根据学生表现调整题目难度"""

    # 获取最近 10 次答题记录
    recent_attempts = await get_recent_attempts(user_id, chapter_number, limit=10)

    if not recent_attempts:
        return 3  # 默认中等难度

    # 计算正确率
    correct_rate = sum(a.is_correct for a in recent_attempts) / len(recent_attempts)

    # 根据正确率调整难度
    if correct_rate >= 0.9:
        return 5  # 太简单，提高难度
    elif correct_rate >= 0.7:
        return 4
    elif correct_rate >= 0.5:
        return 3  # 适中
    elif correct_rate >= 0.3:
        return 2
    else:
        return 1  # 太难，降低难度
```

---

## 🚀 实施计划

### Phase 1: 修复现有问题 (1-2 天)

**目标**: 修复 "fail to fetch" 错误

1. **诊断 API 问题**
   ```bash
   # 测试端点是否可访问
   curl http://localhost:8000/api/quiz/questions/3/1

   # 检查数据库
   SELECT * FROM questions WHERE document_id=3 AND chapter_number=1;
   ```

2. **修复前端 API 调用**
   - 检查 `getApiUrl()` 配置
   - 验证认证 token 是否传递
   - 添加更详细的错误日志

3. **降级方案**
   - 如果 API 失败，显示友好提示
   - 提供重试按钮
   - 生成示例题目保证功能可用

---

### Phase 2: 集成 AI 出题 (2-3 天)

**目标**: 实现真正的 AI 智能出题

1. **创建新的 API 端点**
   ```
   POST /api/quiz/generate-questions
   ```

2. **集成 Examiner Agent**
   ```python
   from app.agents.nodes.examiner import ExaminerAgent

   examiner = ExaminerAgent(api_key=settings.DASHSCOPE_API_KEY)
   questions = await examiner.generate_questions(...)
   ```

3. **异步生成流程**
   - 上传文档后自动触发
   - 保存到题目库
   - 前端直接使用

---

### Phase 3: 完善测试流程 (2-3 天)

**目标**: 打通完整的测试 → 评估 → 复习闭环

1. **Session 管理**
   - 创建唯一的测试 session
   - 记录答题过程
   - 支持暂停和继续

2. **实时反馈优化**
   - 即时显示正确/错误
   - 提供详细解析
   - 根据教学风格调整反馈深度

3. **结果页面增强**
   - 能力雷达图动态更新
   - 错题直接加入错题本
   - 一键开始错题练习

---

### Phase 4: 数据分析与优化 (3-5 天)

**目标**: 基于数据持续改进

1. **题目质量分析**
   - 统计每道题的正确率
   - 识别"坏题"（正确率异常）
   - 人工审核低质量题目

2. **学习效果追踪**
   - 章节完成率 vs 测试通过率
   - 学习时长 vs 成绩提升
   - 识别高效学习路径

3. **个性化推荐**
   - 基于错题模式推荐复习内容
   - 建议下一步学习内容
   - 预测学习效果

---

## 📝 数据流程图

```
┌─────────────┐
│  文档上传    │
└──────┬──────┘
       ↓
┌─────────────────┐
│  PDF 解析       │
│  - 提取内容     │
│  - 识别章节     │
└──────┬──────────┘
       ↓
┌─────────────────┐
│  AI 生成题目    │ ← ExaminerAgent
│  - 10道题/章    │
└──────┬──────────┘
       ↓
┌─────────────────┐
│  题目库         │
│  - Question 表  │
└──────┬──────────┘
       ↓
┌─────────────────┐
│  用户开始测试   │
└──────┬──────────┘
       ↓
┌─────────────────┐
│  答题记录       │
│  - QuizAttempt  │
└──────┬──────────┘
       ↓
┌─────────────────┐
│  成绩分析       │
│  - 正确率       │
│  - 能力维度     │
└──────┬──────────┘
       ↓
┌─────────────────┐
│  生成报告       │
│  - 学习建议     │
│  - 错题本       │
└─────────────────┘
```

---

## 🎨 UI/UX 设计建议

### 测试准备页
```
┌─────────────────────────────────┐
│  📝 第1章 章节测试              │
│                                 │
│  本测试包含 10 道题目            │
│  预计用时: 15-20 分钟            │
│                                 │
│  ☐ 我已准备好开始                │
│                                 │
│  [开始测试]                     │
└─────────────────────────────────┘
```

### 答题页
```
┌─────────────────────────────────┐
│  第 3/10 题        ⏱  05:23    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                 │
│  [难度:★★★] [理解力]          │
│                                 │
│  以下哪个是样本空间的定义？      │
│                                 │
│  ○ A. 所有可能结果的集合         │
│  ● B. 部分结果的集合            │
│  ○ C. 必然发生的事件             │
│  ○ D. 不可能发生的事件           │
│                                 │
│  [提交答案]                      │
└─────────────────────────────────┘
```

### 结果页
```
┌─────────────────────────────────┐
│  🎉 测试完成！                  │
│                                 │
│        ╭────╮                  │
│       │ 85%│  8.5/10            │
│        ╰────╯                  │
│                                 │
│  ✅ 通过测试                     │
│                                 │
│  能力分析                        │
│  ├─ 理解力: ████░░ 80%         │
│  ├─ 逻辑推理: ██████ 100%       │
│  ├─ 术语掌握: ███░░ 70%         │
│  └─ 应用能力: ████░░ 80%        │
│                                 │
│  需要复习: 线性方程组             │
│                                 │
│  [查看错题] [下一章] [重新测试] │
└─────────────────────────────────┘
```

---

## 🔧 技术要点

### 1. 错误处理
```typescript
// 前端优雅降级
const loadQuestions = async () => {
  try {
    const response = await fetch(apiUrl)
    if (!response.ok) throw new Error('API 错误')
    return await response.json()
  } catch (error) {
    // 显示友好错误
    toast.error('加载题目失败，请重试')

    // 提供重试选项
    return {
      questions: generateFallbackQuestions(),
      isFallback: true
    }
  }
}
```

### 2. 进度保存
```typescript
// 防止意外刷新丢失进度
useEffect(() => {
  const saveProgress = throttle(() => {
    localStorage.setItem('quiz_progress', JSON.stringify({
      currentQuestion,
      answers,
      timestamp: Date.now()
    }))
  }, 5000)

  return saveProgress()
}, [currentQuestion, answers])
```

### 3. 性能优化
```python
# 使用缓存减少重复生成
from functools import lru_cache

@lru_cache(maxsize=100)
def get_question_template(difficulty: int, dimension: str):
    """获取题目模板，避免重复生成"""
    ...
```

---

## 📊 成功指标

### 用户体验
- ✅ 测试页面加载时间 < 2 秒
- ✅ 题目生成时间 < 30 秒（或使用预生成）
- ✅ 答题响应时间 < 500ms
- ✅ 结果页面展示完整信息

### 学习效果
- ✅ 测试通过率 >= 60%
- ✅ 错题重做正确率提升 20%
- ✅ 章节完成率提升 30%

### 技术指标
- ✅ API 错误率 < 1%
- ✅ 题目质量合格率 > 95%
- ✅ 数据库查询时间 < 100ms

---

## 🎯 总结

这套章节测试业务方案的核心优势：

1. **AI 驱动** - 智能出题，自适应难度
2. **闭环设计** - 测试 → 评估 → 复习 → 提升
3. **用户体验** - 流畅交互，即时反馈
4. **数据驱动** - 持续优化，个性化推荐

建议优先实施：
1. **Phase 1**: 修复当前 bug
2. **Phase 2**: 集成 AI 出题
3. **Phase 3**: 完善测试流程

需要我开始实施哪个阶段吗？

---

**文档版本**: v1.1.0
**更新时间**: 2026-02-03
**状态**: 基础功能已实现，AI 出题优化中
