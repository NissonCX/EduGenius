# EduGenius - 开发进度

## ✅ 最新完成 (2025-02-11)

### 1. 学习进度更新修复
- 修复 `completion_percentage: null` 问题
- 每次学习对话发送 `completion_percentage: 5`

### 2. 学习日历组件
**新增**: `src/components/calendar/StudyCalendar.tsx`

**设计特点**:
- 符合项目简洁美学风格
- 月份日历网格视图
- 统计卡片：学习天数、总时长、活跃度
- 活动强度等级 0-4（渐进绿色）

**新增API**: `/api/users/{user_id}/activity-calendar?year={year}`

### 3. 题目类型修复
- 后端: 将 AI 返回的 `conceptual` 映射为 `choice`
- 前端: Quiz 组件支持 `conceptual` 类型显示选项

### 4. 学习日历显示修复 ✅
- **问题**: 日历不显示学习记录，尽管用户已学习
- **原因**: `get_or_create_progress()` 创建 Progress 时未设置 `started_at` 字段
- **修复**: 在创建 Progress 时设置 `started_at`, `last_accessed_at`, `created_at`

### 5. 题目内容准确性修复 ✅
- **问题**: 概率论章节出现软件开发相关题目
- **原因**: AI 生成题目时仅使用章节标题，未使用实际内容
- **修复**: `_get_chapter_content_for_generation` 现在使用 ChromaDB 检索实际章节内容
  - 使用 DashScope embedding 进行语义搜索
  - 检索 10 个相关文档片段
  - 将检索到的内容传递给 AI 生成题目

## 待办事项

- [ ] 添加学习日历到仪表盘
- [ ] 测试完整的学习流程
- [ ] 验证题目内容准确性修复效果

## 关键文件
- `src/components/chat/StudyChat.tsx` - 学习进度更新（已修复）
- `src/components/calendar/StudyCalendar.tsx` - 学习日历（新增）
- `src/components/quiz/Quiz.tsx` - 题目显示（已修复）
- `api/app/agents/nodes/examiner.py` - JSON解析器（已修复）
- `api/app/api/endpoints/quiz.py` - 题目API（类型映射已修复）
- `api/app/api/endpoints/users.py` - 活动日历API（新增）
