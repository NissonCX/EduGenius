"""
清理孤立数据脚本
定期清理数据库中的孤立数据（没有关联文档的记录）

运行方式：
    python api/cleanup_orphaned_data.py
"""
import sys
import os
import asyncio

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.core.config import settings


async def cleanup_orphaned_data():
    """清理所有孤立数据"""

    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False
    )

    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        print("\n" + "="*60)
        print("🧹 清理孤立数据脚本")
        print("="*60 + "\n")

        # 1. 清理 progress 表的孤立数据
        print("📊 检查 progress 表...")
        check_progress = text("""
            SELECT COUNT(*) FROM progress
            WHERE document_id NOT IN (SELECT id FROM documents)
        """)
        result = await session.execute(check_progress)
        orphan_progress = result.scalar()
        print(f"   发现 {orphan_progress} 条孤立记录")

        if orphan_progress > 0:
            delete_progress = text("""
                DELETE FROM progress
                WHERE document_id NOT IN (SELECT id FROM documents)
            """)
            await session.execute(delete_progress)
            print(f"   ✅ 已清理 {orphan_progress} 条 progress 记录")

        # 2. 清理 subsections 表的孤立数据
        print("\n📊 检查 subsections 表...")
        check_subsections = text("""
            SELECT COUNT(*) FROM subsections
            WHERE document_id NOT IN (SELECT id FROM documents)
        """)
        result = await session.execute(check_subsections)
        orphan_subsections = result.scalar()
        print(f"   发现 {orphan_subsections} 条孤立记录")

        if orphan_subsections > 0:
            delete_subsections = text("""
                DELETE FROM subsections
                WHERE document_id NOT IN (SELECT id FROM documents)
            """)
            await session.execute(delete_subsections)
            print(f"   ✅ 已清理 {orphan_subsections} 条 subsections 记录")

        # 3. 清理 conversations 表的孤立数据
        print("\n📊 检查 conversations 表...")
        check_conversations = text("""
            SELECT COUNT(*) FROM conversations
            WHERE document_id NOT IN (SELECT id FROM documents)
        """)
        result = await session.execute(check_conversations)
        orphan_conversations = result.scalar()
        print(f"   发现 {orphan_conversations} 条孤立记录")

        if orphan_conversations > 0:
            delete_conversations = text("""
                DELETE FROM conversations
                WHERE document_id NOT IN (SELECT id FROM documents)
            """)
            await session.execute(delete_conversations)
            print(f"   ✅ 已清理 {orphan_conversations} 条 conversations 记录")

        # 4. 清理 quiz_attempts 表的孤立数据
        print("\n📊 检查 quiz_attempts 表...")
        check_quiz = text("""
            SELECT COUNT(*) FROM quiz_attempts
            WHERE progress_id NOT IN (SELECT id FROM progress)
        """)
        result = await session.execute(check_quiz)
        orphan_quiz = result.scalar()
        print(f"   发现 {orphan_quiz} 条孤立记录")

        if orphan_quiz > 0:
            delete_quiz = text("""
                DELETE FROM quiz_attempts
                WHERE progress_id NOT IN (SELECT id FROM progress)
            """)
            await session.execute(delete_quiz)
            print(f"   ✅ 已清理 {orphan_quiz} 条 quiz_attempts 记录")

        # 提交所有更改
        await session.commit()

        print("\n" + "="*60)
        print("✅ 清理完成")
        print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(cleanup_orphaned_data())
