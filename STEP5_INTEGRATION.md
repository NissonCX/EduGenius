# 第五步：前后端集成与功能完善

## 📋 开发流程概览

本阶段将完成以下核心任务，确保 EduGenius 成为可用的完整产品：

```
阶段 1: 打通对话系统 ⚡ (优先级: 🔴 最高)
  ├─ 1.1 创建后端对话 API 端点
  ├─ 1.2 修改前端连接真实后端
  ├─ 1.3 实现 SSE 流式传输
  └─ 1.4 集成 RAG 检索结果

阶段 2: 用户认证系统 🔐 (优先级: 🟡 高)
  ├─ 2.1 后端密码哈希 (bcrypt)
  ├─ 2.2 JWT Token 认证
  ├─ 2.3 创建登录页面
  └─ 2.4 前端状态管理 (Context)

阶段 3: 学习进度追踪 📊 (优先级: 🟢 中)
  ├─ 3.1 实时进度更新 API
  ├─ 3.2 错题本数据持久化
  ├─ 3.3 能力雷达图动态更新
  └─ 3.4 章节锁定/解锁机制

阶段 4: 测试与优化 🧪 (优先级: 🟢 中)
  ├─ 4.1 端到端流程测试
  ├─ 4.2 错误处理完善
  ├─ 4.3 性能优化
  └─ 4.4 用户体验优化
```

---

## 🎯 阶段 1：打通对话系统

### 任务 1.1：创建后端对话 API 端点

**文件**：`/api/app/api/endpoints/teaching.py`

**需要添加**：
```python
@router.post("/chat")
async def chat_with_tutor(request: ChatRequest):
    """
    简化的对话端点，兼容前端调用格式
    """
    # 创建临时会话
    # 调用 Tutor 智能体
    # 返回 SSE 流式响应
```

**输入格式**：
```json
{
  "message": "什么是向量？",
  "chapter_id": "1",
  "student_level": 3,
  "stream": true
}
```

### 任务 1.2：修改前端 StudyChat 组件

**文件**：`/src/components/chat/StudyChat.tsx`

**修改点**：
- 将 `fetch('/api/teaching/chat')` 改为 `fetch('http://localhost:8000/api/teaching/chat')`
- 适配后端返回格式
- 处理 RAG 检索结果的显示

### 任务 1.3：实现文档来源展示

**功能**：在 AI 回复中显示引用的文档片段

**格式**：
```
【讲解内容】

向量是线性代数的基本概念...

【教材原文参考】
📖 第1页：向量是有方向和大小的量...
📖 第3页：向量可以表示为 v = (x, y)...
```

---

## 🔐 阶段 2：用户认证系统

### 任务 2.1：后端密码哈希

**依赖安装**：
```bash
pip install bcrypt python-jose[cryptography] passlib[bcrypt]
```

**文件**：`/api/app/core/security.py`（新建）

**功能**：
- 密码哈希（bcrypt）
- 密码验证
- JWT Token 生成和验证

### 任务 2.2：JWT 认证端点

**新增端点**：
```python
@router.post("/login")  # 用户登录
@router.post("/logout") # 用户登出
@router.get("/me")      # 获取当前用户信息
```

### 任务 2.3：登录页面

**文件**：`/src/app/login/page.tsx`（新建）

**功能**：
- 邮箱/密码登录表单
- JWT Token 存储
- 登录后跳转

### 任务 2.4：用户状态管理

**文件**：`/src/contexts/AuthContext.tsx`（新建）

**功能**：
- 全局用户状态
- 自动登录（localStorage）
- 登录状态持久化

---

## 📊 阶段 3：学习进度追踪

### 任务 3.1：实时进度更新

**后端**：
- 每次对话后更新 `ConversationHistory`
- 每次答题后更新 `QuizAttempt`
- 计算 `success_rate` 和 `competency_scores`

**前端**：
- 调用 `/api/users/{id}/update-progress`
- 实时更新进度条
- 触发进度条动画

### 任务 3.2：错题本数据持久化

**流程**：
1. 用户答错题目
2. 前端调用 POST `/api/users/{id}/update-progress`
3. 后端记录到 `quiz_attempts` 表
4. 前端从 `/api/users/{id}/history` 获取错题列表
5. 在 `/mistakes` 页面展示

### 任务 3.3：能力雷达图动态更新

**数据来源**：
```python
competency_scores = {
    "comprehension": 基于理解类题目正确率,
    "logic": 基于逻辑类题目正确率,
    "terminology": 基于术语类题目正确率,
    "memory": 基于记忆类题目正确率,
    "application": 基于应用类题目正确率,
    "stability": 基于重复答题正确率
}
```

### 任务 3.4：章节锁定/解锁

**规则**：
- 完成当前章节 80% 才能解锁下一章
- 连续答对 3 题可以跳过当前章节
- 等级提升可以解锁高级章节

---

## 🧪 阶段 4：测试与优化

### 测试清单

#### 功能测试
- [ ] 用户注册流程
- [ ] 用户登录流程
- [ ] 对话功能（SSE 流式）
- [ ] 文档上传和解析
- [ ] RAG 检索准确性
- [ ] 进度条实时更新
- [ ] 错题本记录和查看
- [ ] 能力雷达图更新
- [ ] 等级调整机制

#### 性能测试
- [ ] 文档上传速度（< 10s for 10MB）
- [ ] RAG 检索速度（< 500ms）
- [ ] 对话响应速度（首字 < 2s）
- [ ] 页面加载速度（< 3s）

#### 用户体验测试
- [ ] 移动端适配
- [ ] 错误提示友好
- [ ] 加载状态明确
- [ ] 动画流畅

---

## 📁 文件变更清单

### 新增文件

#### 后端
```
api/
├── app/
│   ├── core/
│   │   └── security.py          # JWT 和密码哈希
│   └── api/endpoints/
│       └── auth.py              # 登录/登出端点
```

#### 前端
```
src/
├── app/
│   └── login/
│       └── page.tsx             # 登录页面
├── contexts/
│   └── AuthContext.tsx          # 用户状态管理
└── hooks/
    └── useAuth.ts               # Auth 认证钩子
```

### 修改文件

#### 后端
```
api/
├── app/
│   ├── api/endpoints/
│   │   ├── teaching.py          # 添加 /chat 端点
│   │   └── users.py             # 添加 /login, /me 端点
│   └── models/
│       └── document.py          # User 表添加 hashed_password
```

#### 前端
```
src/
├── components/
│   └── chat/
│       └── StudyChat.tsx        # 连接真实后端
├── app/
│   ├── layout.tsx               # 添加 AuthProvider
│   └── dashboard/page.tsx       # 使用真实数据
└── lib/
    └── api.ts                   # 添加认证相关 API
```

---

## 🚀 开发时间估算

| 阶段 | 任务 | 预计时间 | 难度 |
|------|------|---------|------|
| 1.1 | 创建对话 API 端点 | 30 min | 🟢 简单 |
| 1.2 | 修改前端连接 | 20 min | 🟢 简单 |
| 1.3 | SSE 流式传输 | 30 min | 🟡 中等 |
| 1.4 | RAG 结果展示 | 20 min | 🟡 中等 |
| 2.1 | 密码哈希 | 20 min | 🟢 简单 |
| 2.2 | JWT 认证 | 40 min | 🟡 中等 |
| 2.3 | 登录页面 | 30 min | 🟢 简单 |
| 2.4 | 状态管理 | 30 min | 🟡 中等 |
| 3.1 | 进度更新 | 30 min | 🟡 中等 |
| 3.2 | 错题本 | 30 min | 🟡 中等 |
| 3.3 | 雷达图 | 20 min | 🟢 简单 |
| 3.4 | 章节锁定 | 30 min | 🟡 中等 |
| 4.1 | 功能测试 | 40 min | 🟡 中等 |
| 4.2 | 错误处理 | 30 min | 🟢 简单 |
| 4.3 | 性能优化 | 30 min | 🟡 中等 |
| 4.4 | UX 优化 | 30 min | 🟢 简单 |

**总计**：约 6-7 小时

---

## 🎯 验收标准

### 阶段 1 完成标志
- ✅ 在 `/study` 页面发送消息能收到真实 AI 回复
- ✅ AI 回复中包含文档来源引用
- ✅ SSE 流式输出流畅

### 阶段 2 完成标志
- ✅ 用户可以注册新账户
- ✅ 用户可以登录
- ✅ 刷新页面后保持登录状态
- ✅ 未登录用户无法访问学习页面

### 阶段 3 完成标志
- ✅ 答题后进度条实时更新
- ✅ 答错题目自动加入错题本
- ✅ 能力雷达图显示真实数据
- ✅ 章节按进度解锁

### 阶段 4 完成标志
- ✅ 所有功能测试通过
- ✅ 无明显性能问题
- ✅ 移动端显示正常
- ✅ 错误提示友好

---

## 📝 注意事项

1. **API 密钥**：确保 `.env` 中配置了 `DASHSCOPE_API_KEY`
2. **CORS**：后端已配置 CORS，允许 `localhost:3000`
3. **数据库**：使用 SQLite，自动创建在 `api/edugenius.db`
4. **调试**：使用 `http://localhost:8000/docs` 测试 API

---

**开始执行！** 🚀
