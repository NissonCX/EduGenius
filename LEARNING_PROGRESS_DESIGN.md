# 学习进度记录系统设计

## 📊 概述

基于对话记忆的智能学习进度追踪系统，通过分析用户与AI导师的对话内容，自动计算学习进度、掌握程度，并提供个性化学习建议。

## 🎯 核心功能

### 1. 对话记忆管理

#### 当前实现状态
- ✅ 后端自动加载最近20条历史对话
- ✅ 历史记录按章节和文档隔离
- ✅ 对话自动保存到数据库（后端处理）
- ✅ 前端完整展示历史对话记录
- ✅ 支持跨会话的上下文记忆

#### 数据结构
```python
ConversationHistory:
  - id: 主键
  - user_id: 用户ID
  - document_id: 文档ID
  - chapter_number: 章节号
  - subsection_id: 小节ID（可选）
  - role: user/assistant
  - content: 对话内容
  - student_level_at_time: 对话时的教学风格
  - created_at: 创建时间
```

---

### 2. 学习进度计算

#### 2.1 进度指标

| 指标 | 计算方式 | 权重 | 状态 |
|------|----------|------|------|
| **对话轮数** | 用户提问次数 | 20% | ✅ 已实现 |
| **对话时长** | 累计学习时间（分钟） | 15% | ✅ 已实现 |
| **对话深度** | 平均问题长度、AI回复长度 | 15% | 🚧 待实现 |
| **知识点覆盖** | 提到的关键概念数量 | 20% | 🚧 待实现 |
| **测试表现** | 章节测试正确率 | 30% | ✅ 已实现 |

#### 2.2 章节完成度计算

```python
def calculate_completion_progress(user_id, document_id, chapter_number):
    """
    计算章节完成度 (0-100%)
    """
    # 1. 获取对话数据
    conversations = get_conversations(user_id, document_id, chapter_number)
    user_messages = [c for c in conversations if c.role == 'user']
    ai_messages = [c for c in conversations if c.role == 'assistant']

    # 2. 计算各项指标
    dialogue_rounds = len(user_messages)

    # 平均对话深度（字数）
    avg_depth = mean([
        len(msg.content) for msg in user_messages + ai_messages
    ]) if conversations else 0

    # 3. 获取测试数据
    quiz_attempts = get_quiz_attempts(user_id, chapter_number)
    quiz_score = calculate_recent_quiz_score(quiz_attempts)

    # 4. 综合计算
    progress = 0

    # 对话轮数（目标：至少10轮）
    if dialogue_rounds >= 10:
        progress += 20
    else:
        progress += (dialogue_rounds / 10) * 20

    # 对话深度（目标：平均50字）
    if avg_depth >= 50:
        progress += 15
    else:
        progress += (avg_depth / 50) * 15

    # 测试表现
    progress += quiz_score * 0.3

    # ... 其他指标

    return min(progress, 100)  # 最大100%
```

---

### 3. 智能进度分析

#### 3.1 学习状态检测

通过对话内容分析，识别学生的学习状态：

| 状态 | 触发条件 | AI 响应策略 | 状态 |
|------|----------|-------------|------|
| **困惑** | 连续3个简短问题、重复提问 | 降低难度，提供更多示例 | 🚧 待实现 |
| **自信** | 问题深入、提出创新性问题 | 提高难度，挑战性内容 | 🚧 待实现 |
| **疲劳** | 回复简短、反应时间增长 | 建议休息，总结当前进度 | 🚧 待实现 |
| **掌握** | 正确回答复杂问题、举一反三 | 建议进入下一章节 | 🚧 待实现 |

#### 3.2 知识点追踪

```python
def extract_keypoints(conversations):
    """
    从对话中提取关键概念
    """
    # 1. 使用 NLP 提取实体和关键词
    keywords = extract_keywords(conversations)

    # 2. 识别用户提问涉及的概念
    user_concepts = []
    for msg in user_messages:
        concepts = identify_concepts(msg.content)
        user_concepts.extend(concepts)

    # 3. 统计概念讨论次数
    concept_frequency = Counter(user_concepts)

    # 4. 判断掌握程度（基于讨论深度和反馈）
    concept_mastery = {}
    for concept in concept_frequency:
        mastery = assess_mastery(concept, conversations)
        concept_mastery[concept] = mastery

    return {
        'discussed': list(concept_frequency.keys()),
        'mastery': concept_mastery,
        'recommendations': generate_recommendations(concept_mastery)
    }
```

---

### 4. 进度可视化

#### 4.1 章节进度卡片

```
┌─────────────────────────────────┐
│ 第1章：线性代数基础              │
│ ━━━━━━━━━━━━━━━ 65%            │
│                                  │
│ 📚 对话 12轮  📖 45分钟          │
│ ✅ 已学：向量、矩阵运算          │
│ ⏳ 学习中：线性方程组             │
│ 🎯 建议：完成例题练习             │
└─────────────────────────────────┘
```

#### 4.2 学习轨迹图

- 时间轴：展示每天的学习时长
- 知识地图：显示已掌握的概念节点
- 能力雷达：六维能力评估实时更新

---

## 🔄 业务流程

### 场景1：正常学习流程

```
1. 用户进入章节
   ├─ 加载历史对话
   ├─ 显示当前进度
   └─ AI 欢迎消息（包含进度提醒）

2. 用户提问
   ├─ 发送问题到后端
   ├─ 后端加载历史记录
   ├─ AI 生成上下文感知的回复
   └─ 保存对话并更新进度

3. 实时进度更新
   ├─ 每轮对话后更新进度条
   ├─ 达到阈值时显示成就
   └─ 检测学习状态并调整策略

4. 完成章节
   ├─ 进度达到 80%+
   ├─ 建议进行章节测试
   └─ 测试通过后解锁下一章
```

### 场景2：离开后返回

```
1. 用户重新进入章节
   ├─ 加载所有历史对话
   ├─ AI 总结上次学习内容
   ├─ 显示当前进度和待完成任务
   └─ 提供继续学习的建议

2. 上下文恢复
   ├─ AI 记住之前讨论的概念
   ├─ 避免重复讲解已掌握内容
   └─ 针对性继续未完成的话题
```

### 场景3：进度异常检测

```
1. 检测到学习停滞
   ├─ 长时间无对话记录
   ├─ 进度长时间不变
   └─ 测试表现下降

2. 触发干预机制
   ├─ AI 主动询问是否需要帮助
   ├─ 提供复习建议
   └─ 调整教学风格
```

---

## 🛠️ API 端点设计

### 已实现端点

#### 1. 获取学习进度
```
GET /api/documents/{doc_id}/progress
参数:
  - user_id: int (从 token 获取)

返回:
{
  "document_id": 3,
  "total_chapters": 10,
  "completed_chapters": 6,
  "overall_progress": 60,
  "chapters": [
    {
      "chapter_number": 1,
      "title": "第一章",
      "completion_percentage": 75,
      "dialogue_rounds": 12,
      "study_time_minutes": 45
    }
  ]
}
```

#### 2. 获取对话历史
```
GET /api/teaching/history
参数:
  - document_id: int
  - chapter_number: int
  - subsection_id: int (可选)

返回:
{
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "...",
      "created_at": "2026-02-01T10:30:00"
    }
  ]
}
```

### 计划中端点

#### 3. 获取学习分析
```
GET /api/teaching/progress-analysis
参数:
  - user_id: int
  - document_id: int
  - chapter_number: int

返回:
{
  "completion_percentage": 65,
  "dialogue_rounds": 12,
  "study_time_minutes": 45,
  "keypoints_learned": ["向量", "矩阵运算"],
  "keypoints_learning": ["线性方程组"],
  "mastery_level": "intermediate",
  "recommendations": [
    "建议完成第3节的例题练习",
    "可以尝试一些应用题"
  ]
}
```

#### 4. 智能复习建议
```
GET /api/teaching/review-suggestions
参数:
  - user_id: int

返回:
{
  "weak_points": [
    {
      "concept": "线性方程组",
      "mastery": 0.4,
      "reason": "测试中错误率较高"
    }
  ],
  "suggested_review": [
    "复习第1章第3节：线性方程组",
    "完成相关练习题"
  ]
}
```

---

## 📈 实施状态

### Phase 1: 基础功能（已完成）
- ✅ 对话历史加载和保存
- ✅ 基础进度计算
- ✅ 进度可视化组件
- ✅ 仪表板展示

### Phase 2: 智能分析（进行中）
- 🚧 对话内容分析（关键词提取）
- 🚧 学习状态检测
- ⏳ 知识点追踪

### Phase 3: 个性化推荐（计划中）
- ⏳ 智能复习建议
- ⏳ 自适应学习路径
- ⏳ 学习报告生成

### Phase 4: 高级功能（未来）
- ⏳ 多模态输入支持（图片、公式）
- ⏳ 协作学习功能
- ⏳ 学习成果认证

---

## 🎨 UI/UX 设计要点

### 1. 进度展示
- 使用直观的进度条和百分比
- 颜色编码：红色(0-30%)、黄色(30-70%)、绿色(70-100%)
- 动画效果：进度增加时平滑过渡

### 2. 历史记录
- 支持折叠/展开长对话
- 高亮关键概念
- 快速跳转到特定话题

### 3. 成就系统
- 学习里程碑徽章
- 连续学习天数统计
- 知识点掌握度可视化

---

## 📝 数据模型

### 主要数据表

#### conversation_history
```python
class ConversationHistory(Base):
    """对话历史记录"""
    __tablename__ = "conversation_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    document_id = Column(Integer, ForeignKey("documents.id"))
    chapter_number = Column(Integer)
    subsection_id = Column(String(50), nullable=True)
    role = Column(String(20))  # user/assistant
    content = Column(Text)
    student_level_at_time = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
```

#### learning_progress
```python
class LearningProgress(Base):
    """学习进度记录"""
    __tablename__ = "learning_progress"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    document_id = Column(Integer, ForeignKey("documents.id"))
    chapter_number = Column(Integer)
    subsection_id = Column(String(50), nullable=True)

    dialogue_rounds = Column(Integer, default=0)
    study_time_minutes = Column(Integer, default=0)
    completion_percentage = Column(Float, default=0.0)

    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

---

## 🔐 隐私和数据安全

- 对话记录加密存储
- 用户可导出/删除历史记录
- 遵守数据保护法规（GDPR等）
- 定期清理过期数据

---

## 🚀 性能优化

- 历史记录分页加载
- 使用缓存减少数据库查询
- 异步处理进度计算
- 索引优化（user_id, chapter_number, created_at）

---

**文档版本**: v1.1.0
**更新时间**: 2026-02-03
**状态**: 基础功能已完成，智能分析开发中
