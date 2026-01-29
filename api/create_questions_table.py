#!/usr/bin/env python3
"""
创建 questions 表的迁移脚本
运行: python create_questions_table.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.models.document import Base
from app.core.config import DATABASE_URL

def create_questions_table():
    """创建 questions 表并添加 question_id 外键到 quiz_attempts"""

    print("连接数据库...")

    # 使用同步 SQLite 驱动
    db_path = os.path.join(os.path.dirname(__file__), "edugenius.db")
    database_url = f"sqlite:///{db_path}"

    # 创建引擎
    engine = create_engine(database_url)

    try:
        with engine.connect() as conn:
            # 检查 questions 表是否已存在
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='questions'"
            ))

            if result.fetchone():
                print("⚠️  questions 表已存在，跳过创建")
            else:
                print("📝 创建 questions 表...")
                # 创建 questions 表
                conn.execute(text("""
                    CREATE TABLE questions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        document_id INTEGER NOT NULL,
                        chapter_number INTEGER NOT NULL,
                        question_type VARCHAR(50) NOT NULL,
                        question_text TEXT NOT NULL,
                        options TEXT,
                        correct_answer VARCHAR(500) NOT NULL,
                        explanation TEXT,
                        difficulty INTEGER DEFAULT 3,
                        competency_dimension VARCHAR(50),
                        created_by VARCHAR(50) DEFAULT 'AI',
                        is_active INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP,
                        FOREIGN KEY (document_id) REFERENCES documents(id),
                        FOREIGN KEY (chapter_number) REFERENCES documents(id)
                    )
                """))
                conn.commit()
                print("✅ questions 表创建成功")

            # 检查 quiz_attempts 表是否有 question_id 列
            result = conn.execute(text("PRAGMA table_info(quiz_attempts)"))
            columns = [row[1] for row in result.fetchall()]

            if 'question_id' not in columns:
                print("📝 为 quiz_attempts 表添加 question_id 列...")
                conn.execute(text("""
                    ALTER TABLE quiz_attempts ADD COLUMN question_id INTEGER
                """))
                conn.commit()
                print("✅ question_id 列添加成功")
            else:
                print("⚠️  quiz_attempts.question_id 列已存在")

            # 创建索引
            print("📝 创建索引...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_questions_document_chapter
                ON questions(document_id, chapter_number)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_questions_type
                ON questions(question_type)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_quiz_attempts_question_id
                ON quiz_attempts(question_id)
            """))
            conn.commit()
            print("✅ 索引创建成功")

        print("\n🎉 迁移完成！")
        print("\n表结构:")
        print("  - questions (题目表)")
        print("  - quiz_attempts (答题记录表，已添加 question_id 外键)")

    except Exception as e:
        print(f"❌ 错误: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(create_questions_table())
