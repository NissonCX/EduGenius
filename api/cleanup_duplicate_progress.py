"""
清理 Progress 表中的重复记录
保留最新的记录，删除旧的
"""
import sqlite3

def cleanup_duplicates():
    """清理重复的 progress 记录"""
    try:
        conn = sqlite3.connect('edugenius.db')
        cursor = conn.cursor()
        
        # 查找重复记录
        cursor.execute("""
            SELECT user_id, document_id, chapter_number, COUNT(*) as count
            FROM progress
            WHERE subsection_number IS NULL
            GROUP BY user_id, document_id, chapter_number
            HAVING COUNT(*) > 1
        """)
        
        duplicates = cursor.fetchall()
        
        if not duplicates:
            print("✅ 没有发现重复记录")
            return
        
        print(f"⚠️  发现 {len(duplicates)} 组重复记录")
        
        # 对每组重复记录，保留最新的，删除旧的
        for user_id, document_id, chapter_number, count in duplicates:
            print(f"   处理: user_id={user_id}, document_id={document_id}, chapter={chapter_number} ({count}条)")
            
            # 获取所有重复记录，按 ID 排序
            cursor.execute("""
                SELECT id FROM progress
                WHERE user_id=? AND document_id=? AND chapter_number=? AND subsection_number IS NULL
                ORDER BY id DESC
            """, (user_id, document_id, chapter_number))
            
            ids = [row[0] for row in cursor.fetchall()]
            
            # 保留第一个（最新的），删除其他
            if len(ids) > 1:
                ids_to_delete = ids[1:]
                placeholders = ','.join('?' * len(ids_to_delete))
                cursor.execute(f"""
                    DELETE FROM progress WHERE id IN ({placeholders})
                """, ids_to_delete)
                print(f"   ✓ 删除了 {len(ids_to_delete)} 条旧记录，保留 ID={ids[0]}")
        
        conn.commit()
        print(f"\n✅ 清理完成！删除了 {sum(c-1 for _, _, _, c in duplicates)} 条重复记录")
        
    except Exception as e:
        print(f"❌ 清理失败: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    cleanup_duplicates()
