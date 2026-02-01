# 学习进度记录系统设计

## 📊 概述

基于对话记忆的智能学习进度追踪系统，通过分析用户与AI导师的对话内容，自动计算学习进度、掌握程度，并提供个性化学习建议。

## 🎯 核心功能

### 1. 对话记忆管理

#### 当前实现
- ✅ 后端自动加载最近20条历史对话
- ✅ 历史记录按章节和文档隔离
- ✅ 对话自动保存到数据库（后端处理）

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

| 指标 | 计算方式 | 权重 |
|------|----------|------|
| **对话轮数** | 用户提问次数 | 20% |
| **对话时长** | 累计学习时间（分钟） | 15% |
| **对话深度** | 平均问题长度、AI回复长度 | 15% |
| **知识点覆盖** | 提到的关键概念数量 | 20% |
| **测试表现** | 章节测试正确率 | 30% |

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

| 状态 | 触发条件 | AI 响应策略 |
|------|----------|-------------|
| **困惑** | 连续3个简短问题、重复提问 | 降低难度，提供更多示例 |
| **自信** | 问题深入、提出创新性问题 | 提高难度，挑战性内容 |
| **疲劳** | 回复简短、反应时间增长 | 建议休息，总结当前进度 |
| **掌握** | 正确回答复杂问题、举一反三 | 建议进入下一章节 |

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

### 新增端点

#### 1. 获取学习分析
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

#### 2. 获取对话摘要
```
GET /api/teaching/conversation-summary
参数:
  - user_id: int
  - chapter_number: int
  - since: datetime (可选)

返回:
{
  "summary": "我们讨论了向量的基本概念和运算...",
  "key_concepts": ["向量", "数量积", "向量积"],
  "user_questions_count": 12,
  "last_discussed": "2026-02-01T10:30:00"
}
```

#### 3. 智能复习建议
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

## 📈 实施优先级

### Phase 1: 基础功能（当前）
- ✅ 对话历史加载和保存
- ✅ 基础进度计算
- ⏳ 进度可视化组件

### Phase 2: 智能分析
- ⏳ 对话内容分析（关键词提取）
- ⏳ 学习状态检测
- ⏳ 知识点追踪

### Phase 3: 个性化推荐
- ⏳ 智能复习建议
- ⏳ 自适应学习路径
- ⏳ 学习报告生成

### Phase 4: 高级功能
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

## 📝 数据模型扩展

### 新增表：LearningMastery

```python
class LearningMastery(Base):
    """知识点掌握度"""
    __tablename__ = "learning_mastery"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    document_id = Column(Integer, ForeignKey("documents.id"))
    chapter_number = Column(Integer)

    concept_name = Column(String(200))  # 概念名称
    mastery_level = Column(Float, default=0.0)  # 0-1
    last_practiced = Column(DateTime)
    practice_count = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
```

### 新增表：LearningSession

```python
class LearningSession(Base):
    """学习会话记录"""
    __tablename__ = "learning_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    document_id = Column(Integer, ForeignKey("documents.id"))
    chapter_number = Column(Integer)
    subsection_id = Column(String(50), nullable=True)

    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    duration_minutes = Column(Integer)

    dialogue_rounds = Column(Integer, default=0)
    concepts_discussed = Column(Text)  # JSON array

    learning_state = Column(String(50))  # confused, confident, tired, mastered
    completion_before = Column(Float)
    completion_after = Column(Float)
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
