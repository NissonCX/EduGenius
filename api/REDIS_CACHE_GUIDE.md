# Redis 缓存系统使用指南

## 概述

EduGenius 现已集成 Redis 缓存系统，用于优化数据库查询性能和 API 响应速度。

## 安装 Redis

### macOS

```bash
# 使用 Homebrew 安装
brew install redis
brew services start redis

# 验证安装
redis-cli ping  # 应该返回 PONG
```

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis

# 验证安装
redis-cli ping
```

### Docker

```bash
# 启动 Redis 容器
docker run -d -p 6379:6379 --name redis redis:alpine

# 验证
docker exec -it redis redis-cli ping
```

### Windows

下载 Redis for Windows 或使用 WSL2。

## 配置

在 `.env` 文件中添加 Redis 配置：

```bash
# Redis 连接配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=              # 如果有密码
REDIS_ENABLED=true           # 设为 false 禁用缓存
```

## 缓存策略

### TTL (过期时间) 配置

| 级别 | 时间 | 适用场景 |
|------|------|----------|
| `short` | 1 分钟 | 频繁变化的数据（进度、状态） |
| `medium` | 5 分钟 | 中等频率变化（文档列表） |
| `long` | 15 分钟 | 较少变化（文档元数据） |
| `very_long` | 1 小时 | 很少变化（章节内容） |
| `daily` | 1 天 | 静态数据 |

## 使用方式

### 1. 使用装饰器（推荐）

```python
from app.core.cache import cache_response, cache_invalidate

# 缓存函数返回值
@cache_response('user_info', ttl='long')
async def get_user_info(user_id: int):
    return await db.query(User).filter(User.id == user_id).first()

# 清除缓存（用于写操作）
@cache_invalidate('user_info')
async def update_user(user_id: int, **data):
    return await db.query(User).filter(User.id == user_id).update(**data)
```

### 2. 使用缓存的 CRUD 函数

```python
from app.crud.cached import (
    get_document_cached,
    get_documents_list_cached,
    invalidate_document_cache
)

# 获取文档信息（自动缓存）
doc = await get_document_cached(document_id, db)

# 清除文档缓存
await invalidate_document_cache(document_id, user_id)
```

### 3. 手动缓存操作

```python
from app.core.cache import cache_get, cache_set, cache_delete

# 手动获取缓存
data = await cache_get('my_key', arg1, arg2)

# 手动设置缓存
await cache_set('my_key', data, ttl='medium', arg1, arg2)

# 手动删除缓存
await cache_delete('my_key', arg1, arg2)

# 批量删除（前缀匹配）
from app.core.cache import cache_delete_pattern
await cache_delete_pattern('user:*')
```

## 缓存键

### 预定义的缓存键

```python
from app.core.cache import CacheKeyBuilder

# 用户相关
CacheKeyBuilder.USER_INFO          # user:info:{user_id}
CacheKeyBuilder.USER_PROGRESS      # user:progress:{user_id}
CacheKeyBuilder.USER_HISTORY       # user:history:{user_id}

# 文档相关
CacheKeyBuilder.DOC_INFO           # doc:info:{doc_id}
CacheKeyBuilder.DOC_CHAPTERS       # doc:chapters:{doc_id}

# 章节相关
CacheKeyBuilder.CHAPTER_INFO       # chapter:info:{doc_id}:{chapter_num}
CacheKeyBuilder.CHAPTER_CONTENT    # chapter:content:{doc_id}:{chapter_num}
```

## 缓存失效策略

### 自动失效

- TTL 过期自动失效
- 写操作后自动清除相关缓存

### 手动失效

```python
# 清除特定键
await cache_delete('prefix', arg1, arg2)

# 清除匹配模式的所有键
await cache_delete_pattern('prefix:*')
```

## 监控和调试

### 检查 Redis 状态

```bash
# 连接到 Redis
redis-cli

# 查看所有键
KEYS *

# 查看特定前缀的键
KEYS doc:*

# 查看键的值
GET doc:info:1

# 查看键的 TTL
TTL doc:info:1

# 清空当前数据库（慎用！）
FLUSHDB
```

### 检查应用日志

启动应用后，查看缓存相关日志：

```
✅ Redis 缓存已启动
✅ 缓存命中: doc_info_1
💾 已缓存: doc_info_1 (TTL: 900s)
🗑️ 已清除文档 1 的所有缓存
```

## 禁用缓存

如果不需要缓存功能，可以在 `.env` 中设置：

```bash
REDIS_ENABLED=false
```

或完全不设置 Redis 相关配置，应用会自动禁用缓存。

## 故障排查

### Redis 连接失败

1. 检查 Redis 是否运行：
   ```bash
   redis-cli ping
   ```

2. 检查配置是否正确：
   ```bash
   # .env 文件
   REDIS_HOST=localhost
   REDIS_PORT=6379
   ```

3. 查看应用日志：
   ```
   ❌ Redis 连接失败: ...
   ⚠️ Redis 缓存未启用
   ```

### 缓存未生效

1. 检查 `REDIS_ENABLED=true`
2. 查看日志确认缓存状态
3. 检查缓存键是否正确

## 性能建议

1. **读多写少的数据**：使用较长的 TTL（如 `very_long`）
2. **频繁变化的数据**：使用较短的 TTL（如 `short`）
3. **用户特定数据**：在缓存键中包含 `user_id`
4. **写操作后**：记得清除相关缓存

## 示例

### 示例 1：缓存文档列表

```python
from app.crud.cached import get_documents_list_cached

# 获取用户文档列表（自动缓存 5 分钟）
documents = await get_documents_list_cached(user_id, db)
```

### 示例 2：带缓存失效的更新操作

```python
from app.crud.cached import invalidate_document_cache

# 更新文档后清除缓存
await update_document(document_id, **data)
await invalidate_document_cache(document_id, user_id)
```

### 示例 3：自定义缓存装饰器

```python
from app.core.cache import cache_response

@cache_response('custom_data', ttl='medium', include_params=['user_id', 'doc_id'])
async def get_custom_data(user_id: int, doc_id: int, other_param: str):
    # only user_id and doc_id will be used for cache key
    return await db.query(...).filter(...).all()
```
