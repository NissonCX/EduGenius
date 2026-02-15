# EduGenius 数据库迁移指南

本指南详细说明了数据库迁移的必要性、执行方法以及故障排查。

## 📋 目录

- [什么是数据库迁移](#什么是数据库迁移)
- [为什么需要迁移](#为什么需要迁移)
- [迁移文件说明](#迁移文件说明)
- [执行迁移](#执行迁移)
- [验证迁移](#验证迁移)
- [回滚迁移](#回滚迁移)
- [常见问题](#常见问题)

---

## 什么是数据库迁移

数据库迁移是修改数据库结构的过程，包括：
- 添加新表
- 添加新字段
- 修改字段类型
- 添加索引
- 修改现有数据

EduGenius 使用独立的 Python 脚本来执行迁移，这些脚本位于 `api/migrations/` 目录。

---

## 为什么需要迁移

### 必须执行的迁移

项目开发过程中，数据模型会不断演进。当你从 GitHub 拉取最新代码后，可能需要执行迁移以保持数据库结构同步。

### 当前必须执行的迁移

1. **add_refresh_token.py**
   - 添加 `refresh_token` 字段到 `users` 表
   - 修复登录 token 刷新功能
   - **不执行此迁移将无法正常登录**

2. **add_subsection_to_questions.py**
   - 添加 `subsection` 字段到 `questions` 表
   - 支持小节级别的学习历史
   - **不执行此迁移将无法查看历史对话**

---

## 迁移文件说明

### 迁移脚本位置

```
api/
└── migrations/
    ├── add_refresh_token.py          # 添加 refresh_token 字段
    ├── add_subsection_to_questions.py # 添加 subsection 字段
    └── add_*.py                      # 其他迁移脚本
```

### 迁移脚本命名规范

- `add_*.py` - 添加字段或表
- `modify_*.py` - 修改字段
- `drop_*.py` - 删除字段或表
- `migrate_*.py` - 数据迁移

---

## 执行迁移

### 首次安装（必须执行）

如果你是首次安装 EduGenius，**必须执行以下迁移**：

```bash
# 1. 初始化数据库
cd api
python3 init_db.py

# 2. 执行所有迁移
cd migrations
python3 add_refresh_token.py
python3 add_subsection_to_questions.py
```

### 更新现有安装

当你从 GitHub 拉取最新代码后：

```bash
cd api/migrations

# 检查是否有新的迁移文件
ls -la *.py

# 执行新的迁移脚本
python3 <new_migration_script>.py
```

### 迁移执行顺序

**重要**: 迁移必须按时间顺序执行，不能跳过！

当前迁移顺序：
1. `add_refresh_token.py` (最早)
2. `add_subsection_to_questions.py` (最新)

---

## 验证迁移

### 方法 1: 检查脚本输出

迁移脚本执行后会显示结果：

```bash
$ python3 add_refresh_token.py
2024-01-15 10:30:00 | INFO | 开始迁移: add_refresh_token
2024-01-15 10:30:01 | INFO | refresh_token 字段已存在，跳过
2024-01-15 10:30:01 | INFO | 迁移完成
```

### 方法 2: 使用 SQLite 命令

```bash
# 进入 api 目录
cd api

# 打开数据库
sqlite3 edugenius.db

# 检查表结构
.schema users

# 退出
.quit
```

你应该看到 `refresh_token` 和 `subsection` 字段。

### 方法 3: 测试功能

1. **测试登录功能**
   - 注册新用户
   - 登录
   - 等待 2 小时（或修改 token 有效期）
   - 刷新页面
   - 如果能自动刷新 token，说明 `add_refresh_token` 迁移成功

2. **测试历史对话**
   - 上传文档并选择章节和小节
   - 进行 AI 对话
   - 切换到其他小节再切换回来
   - 如果对话历史还在，说明 `add_subsection_to_questions` 迁移成功

---

## 回滚迁移

### 警告

**回滚会丢失数据！** 除非你完全理解后果，否则不要执行回滚。

### 回滚方法

```bash
# 1. 停止后端服务
# Ctrl+C 或 ./stop-dev.sh

# 2. 备份数据库
cd api
cp edugenius.db edugenius.db.backup

# 3. 删除数据库
rm edugenius.db

# 4. 重新初始化
python3 init_db.py

# 5. 执行需要的迁移（按顺序）
cd migrations
python3 add_refresh_token.py
```

**注意**: 这会清除所有用户数据、上传的文档、对话历史等。

---

## 常见问题

### Q: 我忘记执行迁移了，现在数据还能恢复吗？

**A**: 可以，但取决于具体情况：

1. **如果只是添加新字段**:
   - 执行迁移即可，不会丢失数据

2. **如果修改了现有字段**:
   - 之前的数据可能受影响
   - 建议备份数据库后再执行迁移

3. **如果不确定**:
   ```bash
   # 先备份
   cd api
   cp edugenius.db edugenius.db.backup

   # 再执行迁移
   cd migrations
   python3 <migration_script>.py
   ```

### Q: 迁移脚本执行失败怎么办？

**A**: 按以下步骤排查：

1. **检查错误信息**
   ```bash
   # 查看完整的错误堆栈
   python3 add_refresh_token.py --verbose
   ```

2. **常见错误类型**

   **错误: "no such table: users"**
   - 原因: 数据库未初始化
   - 解决: 先执行 `python3 init_db.py`

   **错误: "duplicate column name: refresh_token"**
   - 原因: 字段已存在
   - 解决: 可以忽略，迁移已执行过

   **错误: "database is locked"**
   - 原因: 后端服务正在运行
   - 解决: 停止后端服务后再执行迁移

3. **手动检查数据库**
   ```bash
   cd api
   sqlite3 edugenius.db
   .schema users
   .quit
   ```

### Q: 如何知道我需要执行哪些迁移？

**A**: 有几种方法：

1. **查看迁移文件时间戳**
   ```bash
   cd api/migrations
   ls -lt *.py
   ```

2. **检查表结构**
   ```bash
   cd api
   sqlite3 edugenius.db
   .schema users
   .quit
   ```

3. **运行功能测试**
   - 如果登录失败 → 可能需要 `add_refresh_token.py`
   - 如果历史对话丢失 → 可能需要 `add_subsection_to_questions.py`

### Q: 迁移是否需要停机？

**A**:
- **开发环境**: 建议停止后端服务
- **生产环境**: 需要维护窗口，停机执行

```bash
# 停止服务
./stop-dev.sh

# 执行迁移
cd api/migrations
python3 <migration>.py

# 重启服务
./start-dev.sh
```

### Q: 可以跳过某些迁移吗？

**A**:
- **不可以**。每个迁移都可能依赖之前的迁移
- 如果跳过，后续功能可能无法正常工作
- 必须按顺序执行所有迁移

### Q: 迁移会影响现有数据吗？

**A**:
- **添加新字段**: 不会影响现有数据
- **修改字段**: 可能影响，通常会有数据迁移逻辑
- **删除字段**: 会永久丢失该字段的数据

EduGenius 的迁移通常只添加字段，不会删除数据。

### Q: 如何在团队开发中同步迁移？

**A**:
1. **添加新迁移时**:
   - 将迁移脚本提交到 Git
   - 在 README 或 CHANGELOG 中说明

2. **拉取更新后**:
   ```bash
   git pull
   cd api/migrations
   # 检查是否有新的迁移文件
   ls -la *.py
   # 执行新的迁移
   python3 <new_migration>.py
   ```

3. **团队规范**:
   - 迁移脚本必须经过 Code Review
   - 不能修改已执行的迁移脚本
   - 只能添加新的迁移脚本

---

## 迁移脚本开发指南

如果你需要创建自己的迁移脚本：

### 模板

```python
#!/usr/bin/env python3
"""
添加 xxx 字段到 xxx 表

作者: Your Name
日期: YYYY-MM-DD
原因: Explain why this migration is needed
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import get_db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    """执行迁移"""
    logger.info("开始迁移: <migration_name>")

    async for db in get_db():
        try:
            # 检查字段是否已存在
            result = await db.execute(
                text("PRAGMA table_info(users)")
            )
            columns = [row[1] for row in result.fetchall()]

            if '<new_field>' in columns:
                logger.info("<new_field> 字段已存在，跳过")
                return

            # 添加字段
            await db.execute(
                text("ALTER TABLE users ADD COLUMN <new_field> <type>")
            )

            await db.commit()
            logger.info("迁移完成")

        except Exception as e:
            logger.error(f"迁移失败: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(migrate())
```

### 最佳实践

1. **幂等性**: 脚本可以重复执行而不会出错
2. **向后兼容**: 不破坏现有数据
3. **日志记录**: 清晰的日志输出
4. **错误处理**: 完善的异常处理
5. **文档说明**: 注释说明迁移原因

---

## 总结

- ✅ 首次安装**必须执行迁移**
- ✅ 更新代码后检查是否有新迁移
- ✅ 执行迁移前备份数据库
- ✅ 按顺序执行所有迁移
- ❌ 不要跳过迁移
- ❌ 不要修改已执行的迁移脚本

如有疑问，请查阅项目文档或在 GitHub 提 Issue。
