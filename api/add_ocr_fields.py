"""
数据库迁移：添加 OCR 相关字段

为 documents 表添加以下字段：
- has_text_layer: 是否有文本层
- ocr_confidence: OCR 置信度
- current_page: 当前处理页码
- total_pages: 总页数
"""
import sqlite3
import os


def migrate():
    """执行数据库迁移"""

    db_path = "edugenius.db"

    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return

    print(f"📊 开始迁移数据库: {db_path}\n")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(documents)")
        columns = [row[1] for row in cursor.fetchall()]

        # 需要添加的字段
        new_fields = {
            'has_text_layer': 'BOOLEAN DEFAULT 1',
            'ocr_confidence': 'REAL DEFAULT 0.0',
            'current_page': 'INTEGER DEFAULT 0',
            'total_pages': 'INTEGER DEFAULT 0'
        }

        for field, field_type in new_fields.items():
            if field not in columns:
                print(f"   ➕ 添加字段: {field} ({field_type})")
                cursor.execute(
                    f"ALTER TABLE documents ADD COLUMN {field} {field_type}"
                )
            else:
                print(f"   ✓ 字段已存在: {field}")

        conn.commit()
        conn.close()

        print("\n✅ 数据库迁移完成\n")

    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    migrate()
