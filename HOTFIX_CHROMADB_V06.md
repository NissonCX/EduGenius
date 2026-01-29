# 🔧 紧急修复：ChromaDB v0.6.0 兼容性问题

## 问题描述
**错误**: 文档上传失败，提示 "In Chroma v0.6.0, list_collections only returns collection names"  
**状态码**: 500 Internal Server Error  
**影响**: 无法上传文档

---

## 根本原因

ChromaDB 从 v0.5.x 升级到 v0.6.0 后，API 发生了破坏性变更：

### 旧 API (v0.5.x)
```python
# list_collections() 返回 Collection 对象列表
collections = client.list_collections()
names = [col.name for col in collections]  # ✅ 可以访问 .name
```

### 新 API (v0.6.0+)
```python
# list_collections() 直接返回名称字符串列表
names = client.list_collections()  # ✅ 直接是字符串列表
# names = [col.name for col in collections]  # ❌ 错误！
```

---

## 错误代码

在 `api/app/core/chroma.py` 第 47 行：

```python
# ❌ 错误：假设返回的是对象
existing_collections = [col.name for col in chroma_client.list_collections()]
```

---

## 修复方案

使用 `get_collection()` 和异常处理来检查集合是否存在：

```python
def create_document_collection(md5_hash: str) -> str:
    collection_name = get_collection_name(md5_hash)

    # ✅ 正确：使用 get_collection 检查
    try:
        # 尝试获取集合，如果存在则直接返回
        chroma_client.get_collection(collection_name)
        return collection_name
    except Exception:
        # 集合不存在，创建新集合
        chroma_client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        return collection_name
```

---

## 修复文件

- `api/app/core/chroma.py` - 修复 `create_document_collection()` 函数

---

## 测试步骤

### 1. 重启后端
```bash
cd api
# 如果后端正在运行，按 Ctrl+C 停止
uvicorn main:app --reload
```

### 2. 测试文档上传
1. 访问 http://localhost:3000/documents/upload
2. 选择一个 PDF 或 TXT 文件
3. 点击"开始上传"
4. 验证上传成功

### 3. 验证 ChromaDB
```bash
# 检查 ChromaDB 数据目录
ls -la api/chroma_db/

# 应该看到新创建的集合目录
```

---

## ChromaDB v0.6.0 其他变更

### 1. list_collections()
```python
# 旧版本
collections = client.list_collections()
for col in collections:
    print(col.name)  # ❌ 不再支持

# 新版本
collection_names = client.list_collections()
for name in collection_names:
    print(name)  # ✅ 直接是字符串
```

### 2. 获取集合
```python
# 推荐方式
try:
    collection = client.get_collection("my_collection")
except Exception:
    # 集合不存在
    collection = client.create_collection("my_collection")
```

### 3. 检查集合是否存在
```python
# 方法 1：使用 get_collection + 异常处理
def collection_exists(name):
    try:
        client.get_collection(name)
        return True
    except:
        return False

# 方法 2：使用 list_collections
def collection_exists(name):
    return name in client.list_collections()
```

---

## 迁移指南

如果你的代码中有其他使用 `list_collections()` 的地方，需要修改：

### 查找需要修改的代码
```bash
# 在项目中搜索
grep -r "list_collections()" api/
```

### 修改模式
```python
# 旧代码
for col in client.list_collections():
    print(col.name)
    print(col.metadata)

# 新代码
for name in client.list_collections():
    col = client.get_collection(name)
    print(col.name)
    print(col.metadata)
```

---

## 预防措施

### 1. 固定依赖版本
在 `requirements.txt` 中固定 ChromaDB 版本：

```txt
# 如果要使用旧版本
chromadb==0.5.0

# 或者使用新版本（推荐）
chromadb>=0.6.0
```

### 2. 添加版本检查
```python
import chromadb

# 检查版本
print(f"ChromaDB version: {chromadb.__version__}")

# 根据版本使用不同的 API
if chromadb.__version__.startswith("0.5"):
    # 使用旧 API
    pass
else:
    # 使用新 API
    pass
```

### 3. 阅读迁移指南
官方迁移指南：https://docs.trychroma.com/deployment/migration

---

## 相关链接

- [ChromaDB v0.6.0 Release Notes](https://github.com/chroma-core/chroma/releases/tag/0.6.0)
- [ChromaDB Migration Guide](https://docs.trychroma.com/deployment/migration)
- [ChromaDB Documentation](https://docs.trychroma.com/)

---

## 其他可能受影响的功能

检查以下功能是否正常：
- [ ] 文档上传
- [ ] RAG 检索
- [ ] 文档删除
- [ ] 章节查询

---

**修复状态**: ✅ 已完成  
**修复时间**: 2026-01-29  
**版本**: v1.1.3  
**ChromaDB 版本**: 0.6.0+
