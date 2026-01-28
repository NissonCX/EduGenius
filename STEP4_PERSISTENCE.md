# 第四步完成：用户系统与进度持久化

## ✅ 已完成的功能

### 1. 用户注册流程 (`/register`)
- ✅ 三步注册流程
  - 步骤 1：基本信息填写（邮箱、用户名、密码）
  - 步骤 2：能力测评（5 道题目）
  - 步骤 3：等级推荐和账户创建
- ✅ 自动测评 L1-L5 等级
- ✅ 直观的 UI 设计（步骤指示器、进度条）

### 2. 学习进度实时记录
- ✅ 扩展数据库模型
  - `ConversationHistory` - 对话历史表
  - `QuizAttempt` - 题目尝试记录表
- ✅ `/api/users/{id}/update-progress` 端点
  - 支持章节完成记录
  - 支持题目提交记录
  - 自动更新正确率统计

### 3. 历史记录 API (`/api/users/{id}/history`)
- ✅ 返回对话历史
- ✅ 返回用户当前等级
- ✅ 返回能力雷达图数据（六维评分）

### 4. 前端会话恢复
- ✅ 刷新页面时自动加载历史对话
- ✅ 恢复用户等级
- ✅ 加载状态指示器

---

## 📁 新增/修改文件

### 后端
```
api/
├── app/
│   ├── models/
│   │   └── document.py              # ✅ 添加 ConversationHistory, QuizAttempt 表
│   ├── api/endpoints/
│   │   └── users.py                 # ✅ 用户注册、历史记录 API
│   └── schemas/
│       └── user.py                  # ✅ 用户相关数据模型
└── main.py                           # ✅ 添加 users_router
```

### 前端
```
src/
├── app/
│   ├── register/
│   │   └── page.tsx                  # ✅ 注册页面（带能力测评）
└── components/chat/
    └── StudyChat.tsx                 # ✅ 添加历史记录加载
```

---

## 📊 数据库模型

### ConversationHistory（对话历史）
```python
id: int
user_id: int
document_id: int
chapter_number: int
role: str  # 'user' or 'assistant'
content: Text
student_level_at_time: int
created_at: DateTime
```

### QuizAttempt（题目尝试）
```python
id: int
user_id: int
progress_id: int
question_text: Text
user_answer: str
correct_answer: str
is_correct: int
time_spent_seconds: int
created_at: DateTime
```

---

## 🔌 API 端点

### 用户注册
```
POST /api/users/register
Body: {
  "email": "user@example.com",
  "username": "johndoe",
  "password": "hashed_password",
  "cognitive_level": 1  // 可选，默认 L1
}
```

### 能力测评
```
POST /api/users/assess-level
Body: {
  "email": "user@example.com",
  "answers": [1, 2, 3, 4, 5]  // 每题得分 1-5
}
Response: {
  "recommended_level": 3,
  "level_name": "进阶 (Intermediate)",
  "avg_score": 75.0,
  "message": "根据您的答题情况，推荐您从 **进阶 (Intermediate)** (L3) 开始学习"
}
```

### 获取历史记录
```
GET /api/users/{user_id}/history?chapter_number=1
Response: {
  "conversations": [...],
  "user_level": 3,
  "competency_scores": {
    "comprehension": 75,
    "logic": 68,
    "terminology": 82,
    "memory": 90,
    "application": 60,
    "stability": 72
  }
}
```

### 更新进度
```
POST /api/users/{user_id}/update-progress
Body: {
  "action": "submit_quiz" | "complete_chapter",
  "progress_id": 123,
  "question_text": "...",
  "user_answer": "A",
  "correct_answer": "A",
  "is_correct": true
}
```

---

## 🎨 注册页面体验

### 三步流程

**步骤 1：基本信息**
- 邮箱、用户名、密码
- 简洁的表单设计

**步骤 2：能力测评**
- 5 道测评题目
- 每题 5 个选项
- 进度条显示
- 实时答题反馈

**步骤 3：等级推荐**
- 自动计算推荐等级
- 显示等级徽章（🌱📗📘📙🏆）
- 测评得分展示
- 一键开始学习

---

## 🔄 会话恢复流程

```
用户刷新 /study 页面
    ↓
前端请求 /api/users/{id}/history
    ↓
后端返回：
  - 对话历史列表
  - 用户当前等级
  - 能力雷达图数据
    ↓
前端重新渲染：
  - ✅ 恢复对话消息
  - ✅ 更新等级显示
  - ✅ 更新雷达图数据
  - ✅ 保持滚动位置
```

---

## 💾 数据持久化场景

### 场景 1：用户完成章节
```javascript
fetch('/api/users/1/update-progress', {
  method: 'POST',
  body: JSON.stringify({
    action: 'complete_chapter',
    progress_id: 123
  })
})
```

### 场景 2：用户提交答案
```javascript
fetch('/api/users/1/update-progress', {
  method: 'POST',
  body: JSON.stringify({
    action: 'submit_quiz',
    progress_id: 123,
    question_text: '什么是向量？',
    user_answer: '有方向和大小的量',
    correct_answer: '有方向和大小的量',
    is_correct: true
  })
})
```

### 场景 3：刷新页面恢复
```javascript
// 自动加载历史对话
// 自动恢复用户等级
// 自动加载能力数据
```

---

## 📈 用户统计 API

```
GET /api/users/{user_id}/stats
Response: {
  "user_id": 1,
  "username": "johndoe",
  "email": "user@example.com",
  "cognitive_level": 3,
  "total_documents_studied": 2,
  "total_chapters_completed": 5,
  "overall_progress_percentage": 45.5,
  "chapter_counts": {
    "not_started": 3,
    "in_progress": 2,
    "completed": 5,
    "locked": 4
  },
  "total_chapters": 14
}
```

---

## 🎯 能力测评逻辑

### 等级划分标准
| 平均分 | 等级 | 名称 |
|--------|------|------|
| 90-100 | L5 | 专家 |
| 75-89 | L4 | 高级 |
| 60-74 | L3 | 进阶 |
| 40-59 | L2 | 入门 |
| 0-39 | L1 | 基础 |

### 测评题目类型
1. 学习方式偏好
2. 解题能力评估
3. 学习风格选择
4. 重点理解方向
5. 困难处理方式

---

## 🚀 访问地址

**注册页面：** http://localhost:3000/register

**学习页面（会话恢复）：** http://localhost:3000/study

---

## 📦 完整的用户流程

```
新用户
    ↓
访问 /register
    ↓
填写基本信息
    ↓
完成能力测评（5 题）
    ↓
系统推荐 L1-L5 等级
    ↓
创建账户
    ↓
跳转到 /study
    ↓
开始学习（历史已记录）
```

---

## ⚙️ 待集成功能

### 前端需要添加：
- [ ] 登录页面 (`/login`)
- [ ] 用户状态管理（Context/Redux）
- [ ] 实时进度更新 UI
- [ ] 更新完成后刷新会话

### 后端需要添加：
- [ ] 密码哈希（bcrypt）
- [ ] JWT Token 认证
- [ ] 会话管理
- [ ] 权限控制

---

**第四步完成！用户系统和进度持久化已实现** 🎉

**可以访问 /register 体验完整的注册流程！**
