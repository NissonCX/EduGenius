"""
数据库迁移：为 users 表添加 refresh_token 字段

运行方式：
    python migrations/add_refresh_token.py
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.database import get_db


async def upgrade():
    """添加 refresh_token 列"""
    async for db in get_db():
        try:
            # 检查列是否已存在
            check_sql = text("""
                SELECT COUNT(*) as count
                FROM pragma_table_info('users')
                WHERE name='refresh_token'
            """)
            result = await db.execute(check_sql)
            row = result.fetchone()
            column_exists = row[0] > 0 if row else False

            if column_exists:
                print("✅ refresh_token 列已存在，跳过迁移")
                return

            # 添加列
            print("📝 正在添加 refresh_token 列...")
            alter_sql = text("""
                ALTER TABLE users
                ADD COLUMN refresh_token VARCHAR(500)
            """)
            await db.execute(alter_sql)
            await db.commit()

            print("✅ 迁移完成：refresh_token 列已添加")

        except Exception as e:
            print(f"❌ 迁移失败: {e}")
            await db.rollback()
            raise


async def downgrade():
    """移除 refresh_token 列（回滚）"""
    async for db in get_db():
        try:
            print("📝 正在移除 refresh_token 列...")
            alter_sql = text("""
                ALTER TABLE users
                DROP COLUMN refresh_token
            """)
            await db.execute(alter_sql)
            await db.commit()
            print("✅ 回滚完成：refresh_token 列已移除")

        except Exception as e:
            print(f"❌ 回滚失败: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="数据库迁移：添加 refresh_token 字段")
    parser.add_argument("--downgrade", action="store_true", help="回滚迁移")
    args = parser.parse_args()

    if args.downgrade:
        print("🔄 开始回滚迁移...")
        asyncio.run(downgrade())
    else:
        print("🚀 开始迁移...")
        asyncio.run(upgrade())
