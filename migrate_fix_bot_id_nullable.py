"""
Migration to fix bot_id nullable constraint
SQLite doesn't support ALTER COLUMN, so we need to recreate the table
"""
import sqlite3
from pathlib import Path


def migrate_database():
    """Fix bot_id to be nullable in documents table"""
    db_path = Path("midas.db")
    
    if not db_path.exists():
        print("❌ Database file not found: midas.db")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        print("🔄 Starting bot_id nullable migration...")
        
        # Check if we need to migrate
        cursor.execute("PRAGMA table_info(documents)")
        columns = {col[1]: col for col in cursor.fetchall()}
        
        # Check if bot_id is NOT NULL
        bot_id_col = columns.get('bot_id')
        if bot_id_col and bot_id_col[3] == 1:  # notnull = 1
            print("📝 bot_id is currently NOT NULL, migrating...")
            
            # Create new table with correct schema
            cursor.execute("""
                CREATE TABLE documents_new (
                    id TEXT PRIMARY KEY,
                    bot_id TEXT,
                    conversation_id TEXT,
                    user_id TEXT,
                    filename TEXT NOT NULL,
                    content TEXT NOT NULL,
                    chunk_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (bot_id) REFERENCES bots(id),
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            print("  ✅ Created new documents table")
            
            # Copy data from old table
            cursor.execute("""
                INSERT INTO documents_new 
                SELECT id, bot_id, conversation_id, user_id, filename, content, chunk_count, created_at
                FROM documents
            """)
            print("  ✅ Copied existing data")
            
            # Drop old table
            cursor.execute("DROP TABLE documents")
            print("  ✅ Dropped old table")
            
            # Rename new table
            cursor.execute("ALTER TABLE documents_new RENAME TO documents")
            print("  ✅ Renamed new table")
            
            # Recreate indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_bot_id ON documents(bot_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_conversation_id ON documents(conversation_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id)")
            print("  ✅ Recreated indexes")
            
            conn.commit()
            print("✅ Migration completed successfully!")
            print("   bot_id is now nullable - conversation-level documents will work!")
        else:
            print("✅ bot_id is already nullable, no migration needed")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_database()
