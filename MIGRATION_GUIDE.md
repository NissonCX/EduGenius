# 数据库迁移执行指南

本文档说明如何执行数据库迁移，解决常见的数据库结构问题。

## 为什么需要迁移？

项目在开发过程中，数据库结构发生了变化。如果你刚克隆项目，需要执行迁移脚本才能正常运行。

## 快速修复

### 一键执行所有迁移

```bash
cd api/migrations
python3 add_refresh_token.py
python3 add_subsection_to_questions.py
python3 add_indexes.py
```

### 验证迁移结果

```bash
cd api
sqlite3 edugenius.db

# 验证 users 表
PRAGMA table_info(users);
# 应该看到: refresh_token 列

# 验证 questions 表
PRAGMA table_info(questions);
# 应该看到: subsection_number 列

.quit
```

## 各迁移脚本说明

### 1. add_refresh_token.py

**问题:** 登录/注册功能失败
**错误信息:** `no such column: users.refresh_token`

**脚本内容:**
```python
import sqlite3

conn = sqlite3.connect('edugenius.db')
cursor = conn.cursor()

try:
    cursor.execute('ALTER TABLE users ADD COLUMN refresh_token VARCHAR')
    conn.commit()
    print('✅ 已添加 refresh_token 列')
except sqlite3.OperationalError as e:
    if 'duplicate column' in str(e):
        print('✓ refresh_token 列已存在')
    else:
        raise

conn.close()
```

### 2. add_subsection_to_questions.py

**问题:** 获取历史对话失败
**错误信息:** `no such column: questions.subsection_number`

**脚本内容:**
```python
import sqlite3

conn = sqlite3.connect('edugenius.db')
cursor = conn.cursor()

try:
    cursor.execute('ALTER TABLE questions ADD COLUMN subsection_number INTEGER')
    conn.commit()
    print('✅ 已添加 subsection_number 列')
except sqlite3.OperationalError as e:
    if 'duplicate column' in str(e):
        print('✓ subsection_number 列已存在')
    else:
        raise

conn.close()
```

### 3. add_indexes.py

**问题:** 性能优化（非必需）

**作用:** 为常用查询字段添加索引，提升查询速度

## 手动 SQL 迁移

如果 Python 脚本无法运行，可以直接使用 SQL：

```bash
cd api
sqlite3 edugenius.db
```

```sql
-- 添加 refresh_token 列
ALTER TABLE users ADD COLUMN refresh_token VARCHAR;

-- 添加 subsection_number 列
ALTER TABLE questions ADD COLUMN subsection_number INTEGER;

-- 验证
.schema users
.schema questions

-- 退出
.quit
```

## 完全重置数据库（最后手段）

如果迁移失败，可以完全重建数据库：

⚠️ **警告:** 这会删除所有数据！

```bash
cd api

# 1. 删除旧数据库
rm edugenius.db
rm edugenius.db-shm
rm edugenius.db-wal

# 2. 重新初始化
python3 init_db.py

# 3. 执行迁移
cd migrations
python3 add_refresh_token.py
python3 add_subsection_to_questions.py
python3 add_indexes.py

# 4. 创建测试用户
curl -X POST http://localhost:8000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@edugenius.com",
    "username": "demo",
    "password": "Demo1234",
    "preferred_teaching_style": 3
  }'
```

## 检查数据库状态

```bash
cd api
sqlite3 edugenius.db
```

```sql
-- 查看所有表
.tables

-- 查看用户
SELECT id, email, username FROM users;

-- 查看文档
SELECT id, title FROM documents;

-- 退出
.quit
```

## 常见错误排查

### 错误 1: "unable to open database file"

**原因:** 数据库文件不存在或权限问题

**解决:**
```bash
cd api
ls -la edugenius.db
# 如果不存在，运行: python3 init_db.py
```

### 错误 2: "no such table: users"

**原因:** 数据库未初始化

**解决:**
```bash
cd api
python3 init_db.py
```

### 错误 3: "database is locked"

**原因:** 后端服务正在运行

**解决:** 停止后端服务后再执行迁移

---

**文档版本:** 1.0
**最后更新:** 2026-02-04
