"""
Authentication utilities for CineSense
Database-backed with JSON fallback for backward compatibility
"""

import json
import os
from typing import Optional, Dict
from backend.database import get_db, User

# Paths for JSON fallback
# Go up two levels from backend/utils/ to reach project root, then into data/
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
USERS_JSON = os.path.join(DATA_DIR, 'users_db.json')
SESSION_JSON = os.path.join(DATA_DIR, 'session.json')

os.makedirs(DATA_DIR, exist_ok=True)


def load_users() -> Dict:
    """Load users from database or JSON fallback"""
    try:
        with get_db() as db:
            users = db.query(User).all()
            return {
                u.email: {
                    'name': u.name,
                    'age': u.age,
                    'gender': u.gender,
                    'genre': u.preferred_genre,
                    'password': u.password
                }
                for u in users
            }
    except Exception as e:
        print(f"⚠️ Database error in load_users: {e}, using JSON")
        if os.path.exists(USERS_JSON):
            with open(USERS_JSON, 'r') as f:
                return json.load(f)
        return {}


def save_users(users_dict: Dict):
    """Save users to database and JSON backup"""
    # Save to JSON for backup
    with open(USERS_JSON, 'w') as f:
        json.dump(users_dict, f, indent=4)
    
    # Save to database
    try:
        with get_db() as db:
            for email, data in users_dict.items():
                user = db.query(User).filter_by(email=email).first()
                if user:
                    # Update existing user
                    user.name = data.get('name', user.name)
                    user.age = data.get('age', user.age)
                    user.gender = data.get('gender', user.gender)
                    user.preferred_genre = data.get('genre', user.preferred_genre)
                    user.password = data.get('password', user.password)
                else:
                    # Create new user
                    user = User(
                        email=email,
                        name=data.get('name', 'Unknown'),
                        password=data.get('password', ''),
                        age=data.get('age'),
                        gender=data.get('gender'),
                        preferred_genre=data.get('genre')
                    )
                    db.add(user)
            db.commit()
    except Exception as e:
        print(f"⚠️ Database error in save_users: {e}")


def load_session() -> Optional[str]:
    """Load current session (logged-in user email)"""
    if not os.path.exists(SESSION_JSON):
        return None
    
    try:
        with open(SESSION_JSON, 'r') as f:
            data = json.load(f)
            return data.get('email')
    except:
        return None


def save_session(email: str):
    """Save current session"""
    with open(SESSION_JSON, 'w') as f:
        json.dump({'email': email}, f)


def clear_session():
    """Clear current session"""
    if os.path.exists(SESSION_JSON):
        os.remove(SESSION_JSON)


def get_user_by_email(email: str) -> Optional[Dict]:
    """Get user data by email from database"""
    try:
        with get_db() as db:
            user = db.query(User).filter_by(email=email).first()
            if user:
                return {
                    'email': user.email,
                    'name': user.name,
                    'age': user.age,
                    'gender': user.gender,
                    'genre': user.preferred_genre
                }
    except Exception as e:
        print(f"⚠️ Database error in get_user_by_email: {e}")
    
    # Fallback to JSON
    users = load_users()
    if email in users:
        return {**users[email], 'email': email}
    return None


def authenticate_user(email: str, password: str) -> bool:
    """Authenticate user credentials"""
    try:
        with get_db() as db:
            user = db.query(User).filter_by(email=email, password=password).first()
            return user is not None
    except Exception as e:
        print(f"⚠️ Database error in authenticate_user: {e}")
        # Fallback to JSON
        users = load_users()
        return email in users and users[email].get('password') == password

