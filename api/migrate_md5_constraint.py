"""
Migration script to change md5_hash from unique to composite unique (md5_hash + uploaded_by)
This allows multiple users to upload the same document while still preventing duplicates per user.
"""
import sqlite3

def migrate_database():
    """Migrate the database schema"""
    conn = sqlite3.connect('edugenius.db')
    cursor = conn.cursor()
    
    try:
        print("🔄 Starting migration...")
        
        # 1. Create new table with correct schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                md5_hash VARCHAR(32) NOT NULL,
                filename VARCHAR(255) NOT NULL,
                file_type VARCHAR(50) NOT NULL,
                file_size INTEGER,
                title VARCHAR(500),
                total_pages INTEGER DEFAULT 0,
                total_chapters INTEGER DEFAULT 0,
                processing_status VARCHAR(50) DEFAULT 'pending',
                chroma_collection_name VARCHAR(100),
                uploaded_by INTEGER,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                FOREIGN KEY (uploaded_by) REFERENCES users(id),
                UNIQUE (md5_hash, uploaded_by)
            )
        """)
        
        # 2. Copy data from old table
        cursor.execute("""
            INSERT INTO documents_new 
            SELECT * FROM documents
        """)
        
        # 3. Drop old table
        cursor.execute("DROP TABLE documents")
        
        # 4. Rename new table
        cursor.execute("ALTER TABLE documents_new RENAME TO documents")
        
        # 5. Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_documents_md5_hash ON documents(md5_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_documents_id ON documents(id)")
        
        conn.commit()
        print("✅ Migration completed successfully!")
        print("   - Changed md5_hash from UNIQUE to composite UNIQUE (md5_hash, uploaded_by)")
        print("   - Multiple users can now upload the same document")
        print("   - Each user can only upload a document once")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
