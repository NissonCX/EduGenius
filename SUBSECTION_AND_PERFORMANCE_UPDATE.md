# 小节支持和性能优化更新

## 完成时间
2026-01-29

## 更新内容

### 1. 数据库层 - 小节支持 ✅

#### 新增表结构
```sql
CREATE TABLE subsections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    chapter_number INTEGER NOT NULL,
    subsection_number INTEGER NOT NULL,
    subsection_title VARCHAR(500),
    content_summary TEXT,
    estimated_time_minutes INTEGER DEFAULT 15,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    UNIQUE (document_id, chapter_number, subsection_number)
);
```

#### Progress 表扩展
- 新增字段：`subsection_number` - 当前学习的小节编号
- 新增字段：`subsection_progress` - 小节学习进度（0-100）

#### 迁移脚本
- 文件：`api/create_subsections_table.py`
- 状态：✅ 已执行成功

### 2. 后端 API - 小节功能 ✅

#### 新增模型
- `api/app/models/subsection.py` - Subsection 数据模型
- `api/app/schemas/subsection.py` - Pydantic 验证模式

#### 更新章节划分服务
- 文件：`api/app/services/chapter_divider.py`
- 功能：LLM 现在会同时提取章节和小节
- 提示词：更新为包含小节识别的指令
- 数据保存：自动创建 Subsection 记录

#### 新增 API 端点
```python
GET /api/documents/{document_id}/chapters/{chapter_number}/subsections
```

**响应格式：**
```json
{
  "document_id": 1,
  "chapter_number": 1,
  "chapter_title": "线性代数基础",
  "total_subsections": 4,
  "subsections": [
    {
      "subsection_number": 1,
      "subsection_title": "向量的定义",
      "content_summary": null,
      "estimated_time_minutes": 15,
      "is_completed": false,
      "progress": 0.0
    }
  ]
}
```

### 3. 前端优化 - 内存泄漏修复 ✅

#### StudyChat 组件优化
文件：`src/components/chat/StudyChat.tsx`

**修复内容：**
1. ✅ 添加 `isMounted` 标志防止组件卸载后更新状态
2. ✅ 使用 `AbortController` 取消未完成的请求
3. ✅ 在 useEffect 中添加清理函数
4. ✅ 移除未使用的 props 和 imports
5. ✅ 优化依赖数组，添加 `getAuthHeaders`

**优化前：**
```typescript
useEffect(() => {
  loadHistory()
}, [user.id, chapterId, chapterTitle])
// ❌ 没有清理函数
// ❌ 组件卸载后仍可能更新状态
// ❌ 请求无法取消
```

**优化后：**
```typescript
useEffect(() => {
  let isMounted = true
  const abortController = new AbortController()

  const loadHistory = async () => {
    // ... 使用 isMounted 和 abortController
  }

  loadHistory()

  return () => {
    isMounted = false
    abortController.abort()
  }
}, [user.id, chapterId, chapterTitle, getAuthHeaders])
```

#### 移除未使用的代码
- ❌ 移除 `User`, `Bot` 图标导入
- ❌ 移除 `studentLevel`, `onStrictnessChange`, `documentId` props
- ❌ 移除 `token` 变量

### 4. 学习流程设计

#### 当前流程（3层）
```
1. /study → 选择教材
2. /study?doc=1 → 选择章节
3. /study?doc=1&chapter=1 → 学习对话
```

#### 未来流程（4层）- 待实现
```
1. /study → 选择教材
2. /study?doc=1 → 选择章节
3. /study?doc=1&chapter=1 → 选择小节 ⬅️ 新增
4. /study?doc=1&chapter=1&section=1 → 学习对话
```

### 5. 待实现功能

#### 前端 UI
- [ ] 创建小节选择页面（第3层）
- [ ] 创建 SubsectionCard 组件
- [ ] 添加小节进度显示
- [ ] 添加小节导航（上一节/下一节）
- [ ] 更新 Quiz 页面支持小节级别测试

#### 后端逻辑
- [ ] 更新 Progress 追踪逻辑支持小节
- [ ] 实现小节级别的解锁机制
- [ ] 添加小节完成度计算
- [ ] 更新 Quiz API 支持小节测试

#### 性能优化（待完成）
- [ ] Sidebar.tsx - 移除 resize 事件监听器
- [ ] Documents.tsx - 清理 setTimeout
- [ ] MobileNav.tsx - 清理 resize 监听器
- [ ] StrictnessMenu.tsx - 清理 click 监听器
- [ ] KnowledgeConstellation.tsx - 清理 resize 监听器
- [ ] 使用 React.memo 优化组件
- [ ] 使用 useMemo 和 useCallback
- [ ] 懒加载大型组件

### 6. 技术亮点

#### 智能目录识别
- LLM 同时识别章节和小节结构
- 支持多种目录格式（中文、英文、数字编号）
- 自动去除页码和编号
- 启发式备用方案

#### 内存泄漏防护
- 组件卸载标志（isMounted）
- 请求取消机制（AbortController）
- 完整的清理函数
- 正确的依赖数组

#### 数据库设计
- 复合唯一约束（document_id, chapter_number, subsection_number）
- 级联删除（ON DELETE CASCADE）
- 灵活的进度追踪（支持章节和小节）

### 7. 测试建议

#### 后端测试
```bash
# 测试小节 API
curl -X GET "http://localhost:8000/api/documents/1/chapters/1/subsections" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 前端测试
1. 上传新文档，检查是否创建小节
2. 长时间使用学习页面，监控内存使用
3. 快速切换章节，检查是否有内存泄漏
4. 检查浏览器开发者工具的 Network 面板，确认请求被正确取消

### 8. 性能指标

#### 预期改进
- 内存使用减少 30-50%
- 无内存泄漏警告
- 请求正确取消
- 组件卸载后无状态更新错误

#### 监控方法
```javascript
// Chrome DevTools
// Performance → Record → 使用应用 → Stop
// 查看 Memory 使用情况
```

### 9. 下一步计划

#### 优先级 P0（紧急）
1. 完成其他组件的内存泄漏修复
2. 实现小节选择 UI
3. 测试端到端学习流程

#### 优先级 P1（重要）
1. 添加小节级别的 Quiz
2. 实现小节进度追踪
3. 优化渲染性能（React.memo）

#### 优先级 P2（优化）
1. 懒加载组件
2. 虚拟滚动长列表
3. 添加性能监控

### 10. 文件清单

#### 新增文件
- `api/create_subsections_table.py` - 数据库迁移脚本
- `api/app/models/subsection.py` - Subsection 模型
- `api/app/schemas/subsection.py` - Subsection 模式
- `SUBSECTION_AND_PERFORMANCE_UPDATE.md` - 本文档

#### 修改文件
- `api/app/services/chapter_divider.py` - 添加小节识别
- `api/app/api/endpoints/documents.py` - 添加小节 API
- `src/components/chat/StudyChat.tsx` - 修复内存泄漏
- `src/app/study/page.tsx` - 移除未使用的 props

### 11. 总结

本次更新完成了：
1. ✅ 数据库层面的小节支持
2. ✅ 后端 API 的小节功能
3. ✅ 前端关键组件的内存泄漏修复
4. ✅ 代码清理和优化

为下一步实现完整的小节学习流程打下了坚实的基础。

---

**更新人：** Kiro AI Assistant  
**日期：** 2026-01-29  
**版本：** v1.0
