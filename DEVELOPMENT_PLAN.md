# EduGenius 开发计划文档

**生成日期**: 2026-01-28
**文档版本**: v1.0
**当前真实完成度**: ~40%（之前声称的 85% 虚高）

---

## 📋 执行摘要

经过深入代码审查，发现项目存在以下关键问题：
1. **大量硬编码数据**（userId=1、mockChapters）
2. **内存泄漏风险**（active_sessions 无限增长）
3. **数据持久化缺失**（对话不保存、进度不更新）
4. **认证系统未实际使用**（JWT 未验证）
5. **功能完整性不足**（文档上传、错题本、章节锁定均未实现）

**建议修复顺序**：
1. 🔴 紧急：移除硬编码、修复内存泄漏
2. 🟡 重要：实现数据持久化、JWT 验证
3. 🟢 优化：完善功能、添加测试

---

## 🐛 已发现的 Bug 列表

### 1. 前端硬编码问题

#### 1.1 StudyChat.tsx（第30行）
```typescript
userId?: number
// ...
userId = 1, // 默认用户 ID ❌ 硬编码
```
**影响**: 所有用户都使用 userId=1，数据混乱
**修复**: 从 localStorage 获取真实 userId

#### 1.2 dashboard/page.tsx（第20-21行）
```typescript
const userId = 1  // ❌ 硬编码
const documentId = 1  // ❌ 硬编码
```
**影响**: 仪表盘显示固定用户数据
**修复**: 从 URL 参数或 localStorage 获取

#### 1.3 Sidebar.tsx（第32-38行）
```typescript
const mockChapters: Chapter[] = [
  { id: '1', title: '第一章：线性代数基础', status: 'completed', progress: 100 },
  // ...
]  // ❌ 硬编码章节列表
```
**影响**: 所有用户看到相同的章节进度
**修复**: 从 `/api/users/{id}/progress` 获取真实数据

### 2. 后端硬编码问题

#### 2.1 teaching.py（第418-419行）
```python
temp_state: TeachingState = {
    "user_id": 1,  # ❌ 默认用户
    "document_id": 1,  # ❌ 默认文档
    # ...
}
```
**影响**: 所有对话都关联到 user_id=1
**修复**: 从请求中获取真实 userId

#### 2.2 users.py（第308-315行）
```python
competency_scores = {
    "comprehension": 70,  # ❌ 硬编码默认值
    "logic": 68,
    # ...
}
```
**影响**: 能力评估数据不真实
**修复**: 基于 QuizAttempt 实际计算

### 3. 内存泄漏

#### 3.1 teaching.py（第43行）
```python
active_sessions = {}  # ❌ 内存字典无限增长
```
**影响**: 长时间运行会耗尽内存
**修复**: 实现 TTL 清理机制或使用 Redis

### 4. 数据持久化缺失

#### 4.1 对话历史不保存
**问题**: `/chat` 端点只返回流式数据，不保存到 ConversationHistory 表
**影响**: 用户刷新页面后对话丢失
**修复**: 在对话完成后保存到数据库

#### 4.2 进度更新未调用
**问题**: 虽然有 `/update-progress` 端点，但前端从未调用
**影响**: 进度永远是 0%
**修复**: 前端在完成章节时调用 API

### 5. 认证系统未实际使用

#### 5.1 JWT Token 未验证
**问题**: 虽然 `/login` 返回 Token，但所有 API 都不验证
**影响**: 任何人都可以访问任何用户数据
**修复**: 添加 JWT 中间件

#### 5.2 Token 未传递
**问题**: 前端调用 API 时不携带 Authorization 头
**影响**: 后端无法识别请求者
**修复**: 在 fetch 请求中添加 Token

### 6. 功能缺失

#### 6.1 文档上传功能
**问题**: `/documents/upload` 端点未实现
**影响**: 无法上传真实教材

#### 6.2 错题本功能
**问题**: `/mistakes` 页面使用静态数据
**影响**: 错题记录不存在

#### 6.3 章节锁定机制
**问题**: `status: 'locked'` 只是 UI 状态，无后端逻辑
**影响**: 用户可以访问任意章节

---

## 📊 真实完成度评估

| 模块 | 声称完成度 | 实际完成度 | 差距原因 |
|------|-----------|-----------|---------|
| 前端基础架构 | 100% | 90% | 部分 UI 未连接数据 |
| AI 对话系统 | 100% | 70% | 对话不保存、用户 ID 硬编码 |
| 用户认证系统 | 100% | 40% | JWT 未验证、Token 未使用 |
| 数据持久化 | 100% | 20% | 模型存在但未实际使用 |
| RAG 检索 | 100% | 60% | 无文档上传、ChromaDB 空的 |
| UI 组件库 | 100% | 95% | 少量组件使用 mock 数据 |
| **整体** | **85%** | **~40%** | **大量功能未真正实现** |

---

## 🎯 开发计划

### 阶段 0: 紧急修复（1-2小时）

#### 任务 0.1: 移除前端硬编码
**优先级**: 🔴 最高
**预计时间**: 30分钟
**文件**:
- `src/components/chat/StudyChat.tsx`
- `src/app/dashboard/page.tsx`
- `src/components/layout/Sidebar.tsx`

**实施步骤**:
1. 创建 `useAuth` hook 获取当前用户
2. 从 localStorage 读取 userId、token
3. 替换所有硬编码的 `userId = 1`
4. Sidebar 从 API 获取真实章节列表

#### 任务 0.2: 移除后端硬编码
**优先级**: 🔴 最高
**预计时间**: 30分钟
**文件**:
- `api/app/api/endpoints/teaching.py`

**实施步骤**:
1. ChatRequest 添加 `user_id` 字段
2. 前端传递真实 userId
3. 从数据库获取用户的 document_id
4. 移除默认值

#### 任务 0.3: 修复内存泄漏
**优先级**: 🔴 最高
**预计时间**: 20分钟
**文件**:
- `api/app/api/endpoints/teaching.py`

**实施步骤**:
1. 实现 Session TTL 清理
2. 添加定时清理任务
3. 限制最大 session 数量

#### 任务 0.4: 实现 JWT 验证中间件
**优先级**: 🔴 最高
**预计时间**: 40分钟
**文件**:
- `api/app/core/security.py` (新建)
- `api/app/api/endpoints/*.py` (修改)

**实施步骤**:
1. 实现 `get_current_user` 依赖函数
2. 添加 `verify_token` 函数
3. 在需要认证的端点添加 `Depends(get_current_user)`

---

### 阶段 1: 数据持久化（2-3小时）

#### 任务 1.1: 对话历史保存
**优先级**: 🟡 高
**预计时间**: 60分钟
**文件**:
- `api/app/api/endpoints/teaching.py`
- `src/components/chat/StudyChat.tsx`

**实施步骤**:
1. 后端：在对话完成后保存到 ConversationHistory
2. 前端：在接收完整消息后调用保存接口
3. 实现批量保存优化

#### 任务 1.2: 进度更新集成
**优先级**: 🟡 高
**预计时间**: 45分钟
**文件**:
- `src/components/chat/StudyChat.tsx`
- `src/app/study/page.tsx`

**实施步骤**:
1. 在章节开始时创建 Progress 记录
2. 每次对话后更新 `last_accessed_at`
3. 完成80%内容时标记为 `completed`

#### 任务 1.3: 真实能力评估
**优先级**: 🟡 高
**预计时间**: 45分钟
**文件**:
- `api/app/api/endpoints/users.py`

**实施步骤**:
1. 基于 QuizAttempt 实际计算六维能力
2. 实现题目分类（理解类、逻辑类等）
3. 加权计算正确率

---

### 阶段 2: 功能完善（3-4小时）

#### 任务 2.1: 文档上传实现
**优先级**: 🟢 中
**预计时间**: 90分钟
**文件**:
- `api/app/api/endpoints/documents.py`
- `api/app/services/document_processor.py`

**实施步骤**:
1. 实现文件上传处理
2. PDF/TXT 解析
3. MD5 去重检查
4. ChromaDB 向量化存储

#### 任务 2.2: 错题本功能
**优先级**: 🟢 中
**预计时间**: 60分钟
**文件**:
- `src/app/mistakes/page.tsx`
- `api/app/api/endpoints/users.py`

**实施步骤**:
1. 后端：添加错题查询端点
2. 前端：从 API 获取真实错题
3. 实现错题复习功能

#### 任务 2.3: 章节锁定机制
**优先级**: 🟢 中
**预计时间**: 60分钟
**文件**:
- `api/app/api/endpoints/users.py`
- `src/components/layout/Sidebar.tsx`

**实施步骤**:
1. 定义解锁规则（完成前置章节、正确率达标）
2. 后端：返回章节列表时包含 locked 状态
3. 前端：禁用锁定章节的点击

---

### 阶段 3: 质量提升（2-3小时）

#### 任务 3.1: 错误处理完善
**优先级**: 🟢 中
**预计时间**: 60分钟

**实施步骤**:
1. 统一错误响应格式
2. 前端全局错误处理
3. 用户友好的错误提示

#### 任务 3.2: 性能优化
**优先级**: 🟢 中
**预计时间**: 60分钟

**实施步骤**:
1. 添加数据库索引
2. 实现响应分页
3. 优化 ChromaDB 查询

#### 任务 3.3: 测试覆盖
**优先级**: 🟢 中
**预计时间**: 60分钟

**实施步骤**:
1. API 端到端测试
2. 前端组件测试
3. 集成测试

---

## 📁 文件修改清单

### 紧急修改（阶段 0）

```
src/
├── components/
│   ├── chat/
│   │   └── StudyChat.tsx          [修改] 移除 userId=1
│   └── layout/
│       └── Sidebar.tsx            [修改] 移除 mockChapters
├── app/
│   ├── dashboard/
│   │   └── page.tsx               [修改] 移除硬编码 ID
│   └── study/
│       └── page.tsx               [修改] 传递真实 userId
├── lib/
│   └── api.ts                     [新增] 统一 API 调用
└── hooks/
    └── useAuth.ts                 [新增] 认证 hook

api/
├── app/
│   ├── core/
│   │   └── security.py            [修改] 添加 JWT 验证
│   └── api/endpoints/
│       ├── teaching.py            [修改] 移除硬编码、修复内存泄漏
│       └── users.py               [修改] 添加 get_current_user
```

---

## 🔐 安全建议

### 当前安全问题
1. ❌ JWT Token 未验证
2. ❌ 用户可访问其他用户数据
3. ❌ 无输入验证
4. ❌ 无速率限制
5. ❌ 密码无强度要求

### 建议修复
1. ✅ 实现 JWT 中间件
2. ✅ 添加用户权限检查
3. ✅ Pydantic 数据验证
4. ✅ 添加 slowapi 速率限制
5. ✅ 前端密码强度验证

---

## 📈 成功指标

完成阶段 0 后应达到：
- ✅ 无硬编码用户 ID
- ✅ 所有 API 调用携带 Token
- ✅ 内存使用稳定

完成阶段 1 后应达到：
- ✅ 对话历史持久化
- ✅ 进度实时更新
- ✅ 能力评估基于真实数据

完成阶段 2 后应达到：
- ✅ 可上传真实文档
- ✅ 错题本功能完整
- ✅ 章节按规则解锁

完成阶段 3 后应达到：
- ✅ 错误处理完善
- ✅ 性能达标
- ✅ 测试覆盖率 >60%

---

## 🚀 下一步行动

**立即开始**（按顺序）：
1. 创建 `useAuth` hook
2. 修改 StudyChat 移除硬编码
3. 实现 JWT 验证中间件
4. 修复 active_sessions 内存泄漏

**预计总时间**: 8-12 小时
**完成后真实完成度**: ~75%

---

## 📝 注意事项

1. **向后兼容**: 修改 API 时保持旧格式兼容
2. **数据迁移**: 现有数据需适配新逻辑
3. **测试**: 每个阶段完成后进行测试
4. **文档**: 及时更新 API 文档

---

**文档结束**
