"""
Migration script to add RAG functionality to existing database
Adds:
- use_rag, rag_top_k, rag_similarity_threshold columns to bots table
- documents table
- document_chunks table
"""
import asyncio
import sqlite3
from pathlib import Path


def migrate_database():
    """Add RAG tables and columns to existing database"""
    db_path = Path("midas.db")
    
    if not db_path.exists():
        print("❌ Database file not found: midas.db")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        print("🔄 Starting RAG migration...")
        
        # Add RAG columns to bots table
        print("📝 Adding RAG columns to bots table...")
        try:
            cursor.execute("ALTER TABLE bots ADD COLUMN use_rag INTEGER DEFAULT 0")
            print("  ✅ Added use_rag column")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("  ⚠️ use_rag column already exists")
            else:
                raise
        
        try:
            cursor.execute("ALTER TABLE bots ADD COLUMN rag_top_k INTEGER DEFAULT 5")
            print("  ✅ Added rag_top_k column")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("  ⚠️ rag_top_k column already exists")
            else:
                raise
        
        try:
            cursor.execute("ALTER TABLE bots ADD COLUMN rag_similarity_threshold REAL DEFAULT 0.7")
            print("  ✅ Added rag_similarity_threshold column")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("  ⚠️ rag_similarity_threshold column already exists")
            else:
                raise
        
        # Create documents table
        print("📝 Creating documents table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                bot_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                content TEXT NOT NULL,
                chunk_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bot_id) REFERENCES bots (id)
            )
        """)
        print("  ✅ Created documents table")
        
        # Create document_chunks table
        print("📝 Creating document_chunks table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding TEXT NOT NULL,
                start_char INTEGER NOT NULL,
                end_char INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
            )
        """)
        print("  ✅ Created document_chunks table")
        
        # Create indexes for better performance
        print("📝 Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_bot_id ON documents(bot_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id)")
        print("  ✅ Created indexes")
        
        conn.commit()
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_database()
