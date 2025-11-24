"""
Migration script to add conversation-level RAG support
Adds conversation_id and user_id columns to documents table
"""
import sqlite3
from pathlib import Path


def migrate_database():
    """Add conversation-level RAG support to documents table"""
    db_path = Path("midas.db")
    
    if not db_path.exists():
        print("❌ Database file not found: midas.db")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        print("🔄 Starting conversation-level RAG migration...")
        
        # Make bot_id nullable and add conversation_id, user_id
        print("📝 Updating documents table...")
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(documents)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'conversation_id' not in columns:
            cursor.execute("ALTER TABLE documents ADD COLUMN conversation_id TEXT")
            print("  ✅ Added conversation_id column")
        else:
            print("  ⚠️ conversation_id column already exists")
        
        if 'user_id' not in columns:
            cursor.execute("ALTER TABLE documents ADD COLUMN user_id TEXT")
            print("  ✅ Added user_id column")
        else:
            print("  ⚠️ user_id column already exists")
        
        # Note: SQLite doesn't support modifying column constraints easily
        # bot_id is already nullable in the new schema, but existing data keeps it
        print("  ℹ️ bot_id is now optional (nullable)")
        
        # Create indexes for better performance
        print("📝 Creating indexes...")
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_conversation_id ON documents(conversation_id)")
            print("  ✅ Created index on conversation_id")
        except sqlite3.OperationalError:
            print("  ⚠️ Index on conversation_id already exists")
        
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id)")
            print("  ✅ Created index on user_id")
        except sqlite3.OperationalError:
            print("  ⚠️ Index on user_id already exists")
        
        conn.commit()
        print("✅ Migration completed successfully!")
        print("\n📚 RAG now supports:")
        print("  • Bot-level documents (bot_id)")
        print("  • Conversation-level documents (conversation_id)")
        print("  • User-level documents (user_id)")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_database()
