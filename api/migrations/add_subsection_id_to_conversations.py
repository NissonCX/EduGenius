"""
添加 subsection_id 字段到 conversations 表
执行方法：python3 api/migrations/add_subsection_id_to_conversations.py
"""

import sqlite3
import sys
from pathlib import Path

# 数据库路径
db_path = Path(__file__).parent.parent / "edugenius.db"

def add_subsection_id_column():
    """添加 subsection_id 列到 conversations 表"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. 检查列是否已存在
        cursor.execute("PRAGMA table_info(conversations)")
        columns = [row[1] for row in cursor.fetchall()]
        has_subsection_id = 'subsection_id' in columns

        if has_subsection_id:
            print("✅ subsection_id 列已存在")
        else:
            print("📝 添加 subsection_id 列...")

            # 2. 添加列（使用 ALTER TABLE）
            cursor.execute("""
                ALTER TABLE conversations
                ADD COLUMN subsection_id VARCHAR(50);
            """)

            # 3. 创建索引以提高查询性能
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_conv_subsection
                ON conversations (user_id, document_id, chapter_number, subsection_id);
            """)

            # 4. 提交更改
            conn.commit()

            # 5. 验证
            cursor.execute("PRAGMA table_info(conversations)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'subsection_id' in columns:
                print("✅ subsection_id 列添加成功")
            else:
                print("❌ 添加失败")
                return False

        # 6. 显示表结构
        print("\n📊 当前 conversations 表结构:")
        cursor.execute("PRAGMA table_info(conversations)")
        for row in cursor.fetchall():
            print(f"   {row[1]}: {row[2]}")

        return True

    except sqlite3.Error as e:
        print(f"❌ 数据库错误: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    if add_subsection_id_column():
        print("\n✅ 迁移完成！")
    else:
        print("\n❌ 迁移失败")
        sys.exit(1)
