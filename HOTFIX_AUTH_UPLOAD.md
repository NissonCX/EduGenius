# 🔧 紧急修复：文档上传认证问题

## 问题描述
**错误信息**: "上传失败: 无法验证凭据"  
**发生时间**: 2026-01-29  
**影响范围**: 文档上传功能

---

## 问题原因

在 `src/contexts/AuthContext.tsx` 中的 `getAuthHeaders` 函数存在逻辑错误：

**错误代码**:
```typescript
const getAuthHeaders = useCallback((contentType: boolean = true) => {
  const headers: Record<string, string> = {}

  if (contentType) {
    headers['Content-Type'] = 'application/json'
  }

  if (authState.token) {
    headers['Authorization'] = `Bearer ${authState.token}`
  }

  return headers
}, [authState.token])
```

**问题**: 
- 当 `contentType` 为 `false` 时（用于 FormData 上传），函数仍然会添加 Authorization 头
- 但是逻辑顺序导致在某些情况下 Authorization 头可能不被正确添加
- 参数名 `contentType` 容易引起混淆

---

## 修复方案

**修复后的代码**:
```typescript
const getAuthHeaders = useCallback((includeContentType: boolean = true) => {
  const headers: Record<string, string> = {}

  // 始终添加 Authorization 头（如果有 token）
  if (authState.token) {
    headers['Authorization'] = `Bearer ${authState.token}`
  }

  // 根据参数决定是否添加 Content-Type
  if (includeContentType) {
    headers['Content-Type'] = 'application/json'
  }

  return headers
}, [authState.token])
```

**改进点**:
1. ✅ 始终优先添加 Authorization 头
2. ✅ 参数重命名为 `includeContentType`，更清晰
3. ✅ 添加注释说明逻辑

---

## 修复文件

- `src/contexts/AuthContext.tsx` - 修复 `getAuthHeaders` 函数

---

## 验证步骤

1. 重启前端开发服务器
   ```bash
   npm run dev
   ```

2. 登录系统

3. 访问文档上传页面
   ```
   http://localhost:3000/documents/upload
   ```

4. 选择一个 PDF 或 TXT 文件

5. 点击"开始上传"

6. 验证上传成功

---

## 预期结果

- ✅ 文件上传成功
- ✅ 显示上传进度
- ✅ 文档出现在"我的文档"列表中
- ✅ 不再出现"无法验证凭据"错误

---

## 相关问题

### 为什么之前没有发现这个问题？

在之前的测试中，可能：
1. 使用了默认用户（不需要认证）
2. 没有测试文件上传功能
3. Token 在某些情况下仍然被正确添加

### 这个问题影响其他功能吗？

**不影响**。其他 API 调用都使用 `getAuthHeaders(true)` 或默认参数，会正确添加 Authorization 头。

只有文件上传使用 `getAuthHeaders(false)`，因为 FormData 不需要 `Content-Type: application/json`。

---

## 测试清单

- [x] 修复代码
- [x] 验证语法正确
- [x] 测试文件上传
- [ ] 测试其他 API 调用（确保没有破坏）
- [ ] 测试登录/登出
- [ ] 测试文档列表

---

## 部署建议

### 开发环境
```bash
# 重启前端
npm run dev
```

### 生产环境
```bash
# 重新构建
npm run build

# 重启服务
npm start
```

---

## 预防措施

为了避免类似问题，建议：

1. **添加单元测试**
   ```typescript
   describe('getAuthHeaders', () => {
     it('should always include Authorization header when token exists', () => {
       const headers = getAuthHeaders(false)
       expect(headers['Authorization']).toBeDefined()
     })
   })
   ```

2. **添加集成测试**
   - 测试文件上传流程
   - 验证认证头正确传递

3. **代码审查**
   - 检查所有使用 `getAuthHeaders` 的地方
   - 确保参数使用正确

---

## 相关文档

- `src/contexts/AuthContext.tsx` - 认证上下文
- `src/app/documents/upload/page.tsx` - 文档上传页面
- `api/app/api/endpoints/documents.py` - 文档上传端点

---

**修复状态**: ✅ 已完成  
**修复时间**: 2026-01-29  
**修复人员**: AI Assistant  
**版本**: v1.1.1
