"""
Database Setup Script for CineSense
Run this script to initialize the database and migrate existing data
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import init_db, reset_db
from backend.database.migrate_data import main as migrate_main


def setup_database(reset: bool = False):
    """
    Setup the CineSense database
    
    Args:
        reset: If True, drop all tables and recreate them
    """
    print("=" * 70)
    print("🎬 CineSense Database Setup")
    print("=" * 70)
    
    if reset:
        print("\n⚠️  WARNING: This will delete all existing data!")
        response = input("Are you sure you want to reset the database? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Setup cancelled")
            return
        
        print("\n🔄 Resetting database...")
        reset_db()
    else:
        print("\n🔧 Initializing database...")
        init_db()
    
    print("\n📊 Starting data migration...")
    migrate_main()
    
    print("\n" + "=" * 70)
    print("✅ Database setup complete!")
    print("=" * 70)
    print("\n📝 Next steps:")
    print("  1. Install dependencies: pip install -r requirements.txt")
    print("  2. Run the application: python app.py")
    print("\n💡 Tips:")
    print("  - Database location: data/cinesense.db")
    print("  - To reset database: python setup_database.py --reset")
    print("=" * 70)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup CineSense database')
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset database (WARNING: deletes all data)'
    )
    
    args = parser.parse_args()
    setup_database(reset=args.reset)

