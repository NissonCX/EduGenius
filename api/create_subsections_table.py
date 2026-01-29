"""
创建 Subsections 表的数据库迁移脚本
"""
import sqlite3
import sys

def create_subsections_table():
    """创建 subsections 表"""
    try:
        conn = sqlite3.connect('edugenius.db')
        cursor = conn.cursor()
        
        # 创建 subsections 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subsections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                chapter_number INTEGER NOT NULL,
                subsection_number INTEGER NOT NULL,
                subsection_title VARCHAR(500),
                content_summary TEXT,
                estimated_time_minutes INTEGER DEFAULT 15,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                UNIQUE (document_id, chapter_number, subsection_number)
            )
        ''')
        
        print("✅ 成功创建 subsections 表")
        
        # 为 progress 表添加 subsection 相关字段
        try:
            cursor.execute('''
                ALTER TABLE progress ADD COLUMN subsection_number INTEGER DEFAULT NULL
            ''')
            print("✅ 为 progress 表添加 subsection_number 字段")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("⚠️  subsection_number 字段已存在")
            else:
                raise
        
        try:
            cursor.execute('''
                ALTER TABLE progress ADD COLUMN subsection_progress FLOAT DEFAULT 0.0
            ''')
            print("✅ 为 progress 表添加 subsection_progress 字段")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("⚠️  subsection_progress 字段已存在")
            else:
                raise
        
        conn.commit()
        print("\n✅ 数据库迁移完成！")
        
    except Exception as e:
        print(f"❌ 迁移失败: {str(e)}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    create_subsections_table()
