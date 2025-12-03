#!/usr/bin/env python3
"""
Script to remove a user and all their associated data from the database.
Usage: python scripts/remove_user.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import get_db_session, User, Rating, Watchlist, SearchHistory

def list_all_users():
    """List all users in the database"""
    db = get_db_session()
    users = db.query(User).all()
    
    print("\n" + "="*80)
    print("ALL USERS IN DATABASE")
    print("="*80)
    print(f"{'ID':<5} {'Email':<30} {'Name':<20} {'Age':<5} {'Gender':<10}")
    print("-"*80)
    
    for user in users:
        print(f"{user.id:<5} {user.email:<30} {user.name:<20} {user.age:<5} {user.gender:<10}")
    
    print("-"*80)
    print(f"Total users: {len(users)}\n")
    
    return users

def search_users_by_name(search_term):
    """Search for users by name (case-insensitive)"""
    db = get_db_session()
    users = db.query(User).filter(User.name.ilike(f"%{search_term}%")).all()
    
    if not users:
        print(f"\n❌ No users found matching '{search_term}'")
        return []
    
    print(f"\n🔍 Found {len(users)} user(s) matching '{search_term}':")
    print("-"*80)
    print(f"{'ID':<5} {'Email':<30} {'Name':<20} {'Age':<5} {'Gender':<10}")
    print("-"*80)
    
    for user in users:
        print(f"{user.id:<5} {user.email:<30} {user.name:<20} {user.age:<5} {user.gender:<10}")
    
    print("-"*80)
    return users

def get_user_stats(user_id):
    """Get statistics about a user's data"""
    db = get_db_session()
    
    ratings_count = db.query(Rating).filter_by(user_id=user_id).count()
    watchlist_count = db.query(Watchlist).filter_by(user_id=user_id).count()
    search_count = db.query(SearchHistory).filter_by(user_id=user_id).count()
    
    return {
        'ratings': ratings_count,
        'watchlist': watchlist_count,
        'searches': search_count
    }

def remove_user(user_id):
    """Remove a user and all their associated data"""
    db = get_db_session()
    
    # Get user info
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        print(f"\n❌ User with ID {user_id} not found!")
        return False
    
    # Get stats before deletion
    stats = get_user_stats(user_id)
    
    print(f"\n⚠️  About to delete user:")
    print(f"   ID: {user.id}")
    print(f"   Email: {user.email}")
    print(f"   Name: {user.name}")
    print(f"\n📊 Associated data:")
    print(f"   Ratings: {stats['ratings']}")
    print(f"   Watchlist items: {stats['watchlist']}")
    print(f"   Search history: {stats['searches']}")
    
    confirm = input("\n❓ Are you sure you want to delete this user? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("\n❌ Deletion cancelled.")
        return False
    
    try:
        # Delete associated data
        db.query(Rating).filter_by(user_id=user_id).delete()
        db.query(Watchlist).filter_by(user_id=user_id).delete()
        db.query(SearchHistory).filter_by(user_id=user_id).delete()
        
        # Delete user
        db.delete(user)
        db.commit()
        
        print(f"\n✅ Successfully deleted user '{user.name}' and all associated data!")
        print(f"   - Deleted {stats['ratings']} ratings")
        print(f"   - Deleted {stats['watchlist']} watchlist items")
        print(f"   - Deleted {stats['searches']} search history entries")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error deleting user: {e}")
        return False

def rename_user(user_id):
    """Rename a user"""
    db = get_db_session()
    
    # Get user info
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        print(f"\n❌ User with ID {user_id} not found!")
        db.close()
        return False
    
    print(f"\n📝 Current user details:")
    print(f"   ID: {user.id}")
    print(f"   Email: {user.email}")
    print(f"   Name: {user.name}")
    print(f"   Age: {user.age}")
    print(f"   Gender: {user.gender}")
    
    new_name = input("\n✏️  Enter new name (or press Enter to cancel): ").strip()
    
    if not new_name:
        print("\n❌ Rename cancelled.")
        db.close()
        return False
    
    old_name = user.name
    
    try:
        user.name = new_name
        db.commit()
        print(f"\n✅ Successfully renamed user from '{old_name}' to '{new_name}'!")
        db.close()
        return True
        
    except Exception as e:
        db.rollback()
        db.close()
        print(f"\n❌ Error renaming user: {e}")
        return False


def main():
    print("\n" + "="*80)
    print("🛠️  USER MANAGEMENT TOOL - CineSense")
    print("="*80)
    
    while True:
        print("\nOptions:")
        print("1. List all users")
        print("2. Search users by name")
        print("3. Rename user by ID")
        print("4. Remove user by ID")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            list_all_users()
            
        elif choice == '2':
            search_term = input("\nEnter name to search: ").strip()
            if search_term:
                search_users_by_name(search_term)
            else:
                print("❌ Please enter a search term")
                
        elif choice == '3':
            try:
                user_id = input("\nEnter user ID to rename: ").strip()
                if user_id:
                    rename_user(user_id)
                else:
                    print("❌ Please enter a user ID")
            except ValueError:
                print("❌ Invalid user ID. Please enter a number.")
                
        elif choice == '4':
            try:
                user_id = input("\nEnter user ID to remove: ").strip()
                if user_id:
                    remove_user(user_id)
                else:
                    print("❌ Please enter a user ID")
            except ValueError:
                print("❌ Invalid user ID. Please enter a number.")
                
        elif choice == '5':
            print("\n👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please enter 1-4.")

if __name__ == "__main__":
    main()

# Made with Bob
