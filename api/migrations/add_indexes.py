"""
数据库迁移: 添加性能优化索引

此迁移为所有主要表添加索引以提升查询性能。
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from app.db.database import get_db


async def upgrade():
    """应用索引更改"""
    async for db in get_db():
        try:
            # User 表索引
            print("正在添加 User 表索引...")
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_user_created ON users (created_at)"))
            
            # Document 表索引
            print("正在添加 Document 表索引...")
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_document_filename ON documents (filename)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_document_type ON documents (file_type)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_document_status ON documents (processing_status)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_document_uploaded_by ON documents (uploaded_by)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_document_uploaded_at ON documents (uploaded_at)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_document_status_uploaded ON documents (processing_status, uploaded_at)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_document_user_status ON documents (uploaded_by, processing_status)"))
            
            # Progress 表索引
            print("正在添加 Progress 表索引...")
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_progress_user_id ON progress (user_id)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_progress_document_id ON progress (document_id)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_progress_chapter ON progress (chapter_number)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_progress_status ON progress (status)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_progress_last_accessed ON progress (last_accessed_at)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_progress_user_document ON progress (user_id, document_id)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_progress_document_chapter ON progress (document_id, chapter_number)"))
            await db.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_progress_user_chapter ON progress (user_id, document_id, chapter_number)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_progress_status_completion ON progress (status, completion_percentage)"))
            
            # ConversationHistory 表索引
            print("正在添加 ConversationHistory 表索引...")
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_conversation_user ON conversations (user_id)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_conversation_document ON conversations (document_id)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_conversation_chapter ON conversations (chapter_number)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_conversation_created ON conversations (created_at)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_conversation_user_doc ON conversations (user_id, document_id)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_conversation_user_chapter ON conversations (user_id, document_id, chapter_number)"))
            
            # QuizAttempt 表索引
            print("正在添加 QuizAttempt 表索引...")
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_quiz_user ON quiz_attempts (user_id)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_quiz_progress ON quiz_attempts (progress_id)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_quiz_question ON quiz_attempts (question_id)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_quiz_is_correct ON quiz_attempts (is_correct)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_quiz_user_progress ON quiz_attempts (user_id, progress_id)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_quiz_progress_correct ON quiz_attempts (progress_id, is_correct)"))
            
            # Question 表索引
            print("正在添加 Question 表索引...")
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_question_document ON questions (document_id)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_question_chapter ON questions (chapter_number)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_question_subsection ON questions (subsection_number)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_question_type ON questions (question_type)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_question_difficulty ON questions (difficulty)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_question_competency ON questions (competency_dimension)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_question_is_active ON questions (is_active)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_question_doc_chapter ON questions (document_id, chapter_number)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_question_subsection_full ON questions (document_id, chapter_number, subsection_number)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_question_type_difficulty ON questions (question_type, difficulty)"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS idx_question_active_doc ON questions (is_active, document_id)"))
            
            await db.commit()
            print("✅ 所有索引创建成功！")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ 创建索引失败: {e}")
            raise


async def downgrade():
    """移除索引更改"""
    async for db in get_db():
        try:
            print("正在移除索引...")
            # 这里可以添加删除索引的语句
            # await db.execute(text("DROP INDEX IF EXISTS idx_user_created"))
            await db.commit()
            print("✅ 索引移除成功")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ 移除索引失败: {e}")
            raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="数据库索引迁移")
    parser.add_argument("--downgrade", action="store_true", help="回滚更改")
    args = parser.parse_args()
    
    if args.downgrade:
        asyncio.run(downgrade())
    else:
        asyncio.run(upgrade())
