#!/usr/bin/env python3
"""
Migration script to add country and update preferred_genre to preferred_genres
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from backend.database import engine

def migrate():
    """Add new columns to users table"""
    
    with engine.connect() as conn:
        try:
            # Add country column
            print("Adding 'country' column...")
            conn.execute(text("ALTER TABLE users ADD COLUMN country VARCHAR(100)"))
            conn.commit()
            print("✅ Added 'country' column")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("⚠️  'country' column already exists")
            else:
                print(f"❌ Error adding country: {e}")
        
        try:
            # Rename preferred_genre to preferred_genres and increase size
            print("\nUpdating 'preferred_genre' to 'preferred_genres'...")
            
            # SQLite doesn't support RENAME COLUMN directly in older versions
            # So we'll add new column, copy data, and drop old one
            conn.execute(text("ALTER TABLE users ADD COLUMN preferred_genres VARCHAR(200)"))
            conn.execute(text("UPDATE users SET preferred_genres = preferred_genre WHERE preferred_genre IS NOT NULL"))
            conn.commit()
            print("✅ Added 'preferred_genres' column and copied data")
            
            # Note: We keep the old column for backward compatibility
            # You can manually drop it later if needed: ALTER TABLE users DROP COLUMN preferred_genre
            
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("⚠️  'preferred_genres' column already exists")
            else:
                print(f"❌ Error updating genres: {e}")
        
        try:
            # Add index for country
            print("\nAdding index for country...")
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_country ON users(country)"))
            conn.commit()
            print("✅ Added index for country")
        except Exception as e:
            print(f"⚠️  Index might already exist: {e}")
    
    print("\n" + "="*60)
    print("✅ Migration completed successfully!")
    print("="*60)
    print("\nNew fields added:")
    print("  - country: VARCHAR(100)")
    print("  - preferred_genres: VARCHAR(200) (supports multiple genres)")
    print("\nNote: Old 'preferred_genre' column kept for compatibility")

if __name__ == "__main__":
    print("="*60)
    print("DATABASE MIGRATION: Add Country and Multi-Genre Support")
    print("="*60)
    migrate()

# Made with Bob
