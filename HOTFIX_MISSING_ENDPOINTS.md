# 🔧 紧急修复：缺失的文档管理端点

## 问题描述
**错误**: 文档上传失败，提示"无法验证凭据"  
**根本原因**: 前端调用了不存在的 API 端点 `/api/documents/list` 和 `/api/documents/{id}` (DELETE)

---

## 问题分析

### 前端调用的端点
1. `GET /api/documents/list` - 获取文档列表
2. `DELETE /api/documents/{document_id}` - 删除文档

### 后端实际存在的端点
1. `POST /api/documents/upload` - 上传文档
2. `GET /api/documents/{document_id}` - 获取单个文档
3. `GET /api/documents/{document_id}/chapters` - 获取章节列表
4. `POST /api/documents/{document_id}/redivide-chapters` - 重新划分章节
5. `GET /api/documents/health` - 健康检查

**结论**: 缺少文档列表和删除端点！

---

## 修复方案

### 1. 添加文档列表端点

```python
@router.get("/list")
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户上传的所有文档列表"""
    # 查询用户的所有文档
    result = await db.execute(
        select(Document).where(
            Document.uploaded_by == current_user.id
        ).order_by(Document.uploaded_at.desc())
    )
    documents = result.scalars().all()
    
    # 返回文档列表
    return {
        "documents": [...],
        "total": len(documents)
    }
```

### 2. 添加文档删除端点

```python
@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除文档"""
    # 验证文档存在且属于当前用户
    document = await get_document_by_id(document_id)
    
    if document.uploaded_by != current_user.id:
        raise HTTPException(403, "无权限删除此文档")
    
    # 删除文档
    await db.delete(document)
    await db.commit()
    
    return {"message": "文档删除成功"}
```

---

## 修复文件

- `api/app/api/endpoints/documents.py` - 添加 `/list` 和 `DELETE /{document_id}` 端点

---

## 为什么之前没发现？

1. **前后端分离开发**: 前端假设后端有这些端点
2. **缺少 API 文档同步**: 前后端没有共享 API 规范
3. **缺少集成测试**: 没有测试完整的用户流程

---

## 测试步骤

### 1. 重启后端
```bash
cd api
uvicorn main:app --reload
```

### 2. 测试文档列表端点
```bash
# 获取 token（先登录）
TOKEN="your-jwt-token"

# 测试列表端点
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/documents/list
```

### 3. 测试文档删除端点
```bash
# 删除文档
curl -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/documents/1
```

### 4. 测试前端
1. 访问 http://localhost:3000/documents/upload
2. 上传文件
3. 验证文件出现在列表中
4. 点击删除按钮
5. 验证文件被删除

---

## API 文档更新

### GET /api/documents/list

**描述**: 获取当前用户上传的所有文档列表

**认证**: 需要 Bearer Token

**响应**:
```json
{
  "documents": [
    {
      "id": 1,
      "filename": "example.pdf",
      "title": "示例文档",
      "file_type": "pdf",
      "file_size": 1024000,
      "total_pages": 10,
      "total_chapters": 3,
      "processing_status": "completed",
      "uploaded_at": "2026-01-29T10:00:00",
      "md5_hash": "abc123..."
    }
  ],
  "total": 1
}
```

### DELETE /api/documents/{document_id}

**描述**: 删除指定文档

**认证**: 需要 Bearer Token

**参数**:
- `document_id` (path): 文档 ID

**响应**:
```json
{
  "message": "文档删除成功",
  "document_id": 1
}
```

**错误**:
- `404`: 文档不存在
- `403`: 无权限删除此文档

---

## 预防措施

### 1. API 规范先行
使用 OpenAPI/Swagger 定义 API 规范，前后端共享

### 2. 集成测试
添加端到端测试，覆盖完整用户流程

### 3. API 文档同步
使用 FastAPI 自动生成的文档（/docs）作为参考

### 4. 前端 Mock
在后端未完成时，使用 Mock 数据测试前端

---

## 相关问题

### 为什么上传也失败了？

虽然上传端点存在，但因为前端在加载页面时会先调用 `/list` 端点，如果这个失败了，可能导致认证状态异常。

### 其他端点是否也缺失？

需要检查：
- 用户相关端点
- 测验相关端点
- 错题本相关端点

---

**修复状态**: ✅ 已完成  
**修复时间**: 2026-01-29  
**版本**: v1.1.2
