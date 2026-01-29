"""
为 Progress 表添加唯一约束，防止重复记录
"""
import sqlite3
import sys

def add_unique_constraint():
    """为 progress 表添加唯一约束"""
    try:
        conn = sqlite3.connect('edugenius.db')
        cursor = conn.cursor()
        
        # 检查索引是否已存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name='idx_progress_unique'
        """)
        
        if cursor.fetchone():
            print("⚠️  唯一索引已存在，跳过创建")
            return
        
        # 创建唯一索引
        cursor.execute("""
            CREATE UNIQUE INDEX idx_progress_unique 
            ON progress(user_id, document_id, chapter_number)
            WHERE subsection_number IS NULL
        """)
        
        print("✅ 成功创建 progress 表唯一索引")
        
        # 为包含小节的记录创建另一个唯一索引
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name='idx_progress_subsection_unique'
        """)
        
        if not cursor.fetchone():
            cursor.execute("""
                CREATE UNIQUE INDEX idx_progress_subsection_unique 
                ON progress(user_id, document_id, chapter_number, subsection_number)
                WHERE subsection_number IS NOT NULL
            """)
            print("✅ 成功创建 progress 小节唯一索引")
        
        conn.commit()
        print("\n✅ 数据库约束添加完成！")
        
    except sqlite3.IntegrityError as e:
        print(f"⚠️  发现重复数据: {str(e)}")
        print("请先清理重复数据，然后重新运行此脚本")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 添加约束失败: {str(e)}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    add_unique_constraint()
