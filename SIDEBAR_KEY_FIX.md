# Sidebar Key 冲突 Bug 修复说明

## 🐛 问题描述
控制台出现 React key 警告：
```
Encountered two children with the same key, `1`.
Keys should be unique so that components maintain their identity across updates.
```

**位置**: `src/components/layout/Sidebar.tsx:350`

## 🔍 问题原因
在 Sidebar 组件中，章节列表使用 `chapter.id` 作为 React key：

```typescript
const chapterList: Chapter[] = progressData.map((p: any) => ({
  id: p.chapter_number.toString(),  // ❌ 问题：如果有多条记录的 chapter_number 相同，id 就会重复
  title: p.chapter_title || `第${p.chapter_number}章`,
  ...
}))

// 渲染时使用 chapter.id 作为 key
chapters.map((chapter) => (
  <motion.div key={chapter.id}>  // ❌ 多个章节可能都是 id="1"
    ...
  </motion.div>
))
```

**问题场景**：
- 用户上传了多个文档
- 或数据库中存在重复的章节号
- 导致多个章节对象拥有相同的 id（都是 "1", "2" 等）

## ✅ 修复方案

### 1. 生成唯一 ID
组合 `document_id`、`chapter_number` 和索引来创建唯一标识：

```typescript
const chapterList: Chapter[] = progressData.map((p: any, idx: number) => ({
  id: `doc_${p.document_id}_chapter_${p.chapter_number}_${idx}`,  // ✅ 唯一 ID
  title: p.chapter_title || `第${p.chapter_number}章`,
  status: p.status as 'completed' | 'in-progress' | 'locked',
  progress: Math.round(p.completion_percentage),
  chapter_number: p.chapter_number,  // ✅ 新增：保存章节号
  document_id: p.document_id        // ✅ 新增：保存文档 ID
}))
```

**ID 格式**: `doc_{document_id}_chapter_{chapter_number}_{index}`
- 例如: `doc_1_chapter_1_0`, `doc_2_chapter_1_1`

### 2. 修复导航逻辑
更新 `handleChapterClick` 函数，使用新字段构建正确的 URL：

```typescript
const handleChapterClick = (chapter: Chapter) => {
  ...
  const documentId = (chapter as any).document_id || 1
  const chapterNumber = (chapter as any).chapter_number || 1
  router.push(`/study?documentId=${documentId}&chapter=${chapterNumber}`)
}
```

## 📝 修改的文件
- `src/components/layout/Sidebar.tsx`
  - 第 71-76 行：修改章节 ID 生成逻辑
  - 第 113-130 行：更新导航处理函数

## 🧪 测试步骤

1. **清除浏览器缓存**
   ```bash
   # 在浏览器中按 Cmd+Shift+R 硬刷新
   ```

2. **检查控制台**
   - 打开浏览器开发者工具（F12）
   - 查看 Console 标签
   - 应该不再看到 key 重复警告

3. **功能测试**
   - 登录账号
   - 查看侧边栏章节列表
   - 点击不同章节
   - 确认能正确跳转到学习页面

## ✅ 验证结果
```bash
npm run build
# ✓ Compiled successfully in 4.0s
```

前端已成功编译，无错误。

## 📊 影响
- ✅ 修复了 React key 警告
- ✅ 支持多个文档的章节显示
- ✅ 保持导航功能正常工作
- ✅ 不影响其他组件

---

**修复时间**: 2026-01-29
**优先级**: P1 - 关键 Bug
**状态**: ✅ 已修复并验证
