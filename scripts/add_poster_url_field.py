"""
Migration script to add poster_url field to movies table
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.connection import engine
from sqlalchemy import text

def add_poster_url_field():
    """Add poster_url column to movies table"""
    
    print("Adding poster_url field to movies table...")
    
    with engine.connect() as conn:
        try:
            # Check if column already exists
            result = conn.execute(text("PRAGMA table_info(movies)"))
            columns = [row[1] for row in result]
            
            if 'poster_url' in columns:
                print("✓ poster_url field already exists")
                return
            
            # Add the new column
            conn.execute(text("""
                ALTER TABLE movies 
                ADD COLUMN poster_url VARCHAR(500)
            """))
            conn.commit()
            
            print("✓ Successfully added poster_url field")
            
        except Exception as e:
            print(f"✗ Error adding poster_url field: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    add_poster_url_field()
    print("\nMigration complete!")

# Made with Bob
