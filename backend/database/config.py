"""
Database Configuration and Connection Management
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

# Database configuration
# Go up two levels from backend/database/ to reach project root, then into data/
DATABASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
DATABASE_PATH = os.path.join(DATABASE_DIR, 'cinesense.db')
DATABASE_URL = f'sqlite:///{DATABASE_PATH}'

# Ensure database directory exists
os.makedirs(DATABASE_DIR, exist_ok=True)

# Create engine with optimizations for SQLite
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    connect_args={
        'check_same_thread': False,  # Allow multi-threading
        'timeout': 30  # Connection timeout in seconds
    },
    poolclass=StaticPool,  # Use static pool for SQLite
    pool_pre_ping=True  # Verify connections before using
)

# Enable foreign key constraints for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign keys and optimize SQLite performance"""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for better concurrency
    cursor.execute("PRAGMA synchronous=NORMAL")  # Balance between safety and speed
    cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
    cursor.execute("PRAGMA temp_store=MEMORY")  # Store temp tables in memory
    cursor.close()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create thread-safe scoped session
db_session = scoped_session(SessionLocal)


@contextmanager
def get_db():
    """
    Context manager for database sessions.
    Ensures proper cleanup and error handling.
    
    Usage:
        with get_db() as db:
            user = db.query(User).first()
    """
    session = db_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_db_session():
    """
    Get a database session for Flask dependency injection.
    Must be closed manually or used with try/finally.
    
    Usage:
        db = get_db_session()
        try:
            user = db.query(User).first()
            db.commit()
        finally:
            db.close()
    """
    return db_session()


def init_db():
    """Initialize database tables"""
    from database.models import Base
    Base.metadata.create_all(bind=engine)
    print(f"✅ Database initialized at: {DATABASE_PATH}")


def drop_all_tables():
    """Drop all tables (use with caution!)"""
    from database.models import Base
    Base.metadata.drop_all(bind=engine)
    print("⚠️ All tables dropped!")


def reset_db():
    """Reset database by dropping and recreating all tables"""
    drop_all_tables()
    init_db()
    print("✅ Database reset complete!")


# Cleanup function for application shutdown
def cleanup_db():
    """Clean up database connections"""
    db_session.remove()
    engine.dispose()
    print("✅ Database connections closed")

# Made with Bob
