"""
迁移脚本：为 quiz_attempts 表添加 question_id 列

运行方式：python add_question_id_column.py
"""
import sqlite3
import os

def migrate():
    db_path = os.path.join(os.path.dirname(__file__), 'edugenius.db')

    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return

    print(f"📄 数据库文件: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 检查 question_id 列是否已存在
        cursor.execute("PRAGMA table_info(quiz_attempts)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'question_id' in columns:
            print("✅ question_id 列已存在，无需迁移")
            return

        print("🔄 开始迁移...")

        # 添加 question_id 列
        cursor.execute("""
            ALTER TABLE quiz_attempts
            ADD COLUMN question_id INTEGER
        """)

        print("✅ 已添加 question_id 列")

        # 可选：创建外键约束（需要重建表）
        # SQLite 不支持直接添加外键约束，但可以在应用层保证数据完整性

        conn.commit()
        print("✅ 迁移完成！")

    except Exception as e:
        conn.rollback()
        print(f"❌ 迁移失败: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
