"""
Migration script to add bot_id column to conversations table
Run this once to update existing database
"""
import sqlite3
import sys

def migrate():
    try:
        # Connect to database
        conn = sqlite3.connect('midas.db')
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(conversations)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'bot_id' in columns:
            print("✓ bot_id column already exists")
            return
        
        # Add bot_id column
        print("Adding bot_id column to conversations table...")
        cursor.execute("ALTER TABLE conversations ADD COLUMN bot_id TEXT")
        
        conn.commit()
        print("✓ Migration completed successfully!")
        print("  - Added bot_id column to conversations table")
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 50)
    print("Database Migration: Add bot_id to conversations")
    print("=" * 50)
    migrate()
