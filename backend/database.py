from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
import os
from pathlib import Path
from models import Base
from typing import Generator

# Database configuration
DATABASE_URL = "sqlite:///./ai_interview.db"

# Create database directory if it doesn't exist
db_path = Path("./ai_interview.db")
db_path.parent.mkdir(exist_ok=True)

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False  # Needed for SQLite
    },
    poolclass=StaticPool,
    echo=True  # Set to False in production
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")

def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_session():
    """Context manager for database session"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_database():
    """Initialize database with tables"""
    try:
        create_tables()
        migrate_database()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

def migrate_database():
    """Run database migrations to add new columns"""
    import sqlite3
    
    db_file = "./ai_interview.db"
    if not os.path.exists(db_file):
        return
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # Check if notebook_data column exists
        cursor.execute("PRAGMA table_info(sessions)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'notebook_data' not in columns:
            print("📝 Adding notebook_data column to sessions table...")
            cursor.execute("ALTER TABLE sessions ADD COLUMN notebook_data TEXT")
            conn.commit()
            print("✅ Added notebook_data column")
    except Exception as e:
        print(f"Migration warning: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_database()