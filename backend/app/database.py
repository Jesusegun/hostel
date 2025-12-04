"""
Database Connection & Session Management

This module handles the connection to PostgreSQL using SQLAlchemy.

Why SQLAlchemy?
- ORM (Object-Relational Mapping) - write Python instead of SQL
- Connection pooling (reuses connections for performance)
- Database-agnostic (works with PostgreSQL, MySQL, SQLite)
- Migration support (via Alembic)

Architecture:
    Engine → Connection Pool → Database
    SessionLocal → Individual database sessions (like opening a file)
    Base → Parent class for all database models
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# ===== Database Engine =====
# The engine is like the "phone line" to the database
# It manages the connection pool (reuses connections for speed)

engine = create_engine(
    settings.DATABASE_URL,
    
    # Connection Pool Settings
    pool_pre_ping=True,  # Verify connections before using (handles disconnects)
    pool_size=5,  # Keep 5 connections ready
    max_overflow=10,  # Allow up to 10 extra connections if needed
    
    # Echo SQL queries in development (helpful for debugging)
    echo=settings.DEBUG,
)


# ===== Session Factory =====
# SessionLocal is a factory that creates database sessions
# Think of a session like "opening a file" - you open it, use it, then close it

SessionLocal = sessionmaker(
    autocommit=False,  # Don't auto-save changes (we control when to save)
    autoflush=False,  # Don't auto-send queries (we control when to query)
    bind=engine,  # Connect to our engine
)


# ===== Base Class for Models =====
# All database models (tables) will inherit from this
# Example: class User(Base): ...

Base = declarative_base()


# ===== Dependency Injection =====
# This function is used by FastAPI to provide a database session to routes
# It automatically opens a session, lets you use it, then closes it

def get_db():
    """
    Get Database Session (FastAPI Dependency)
    
    Usage in FastAPI routes:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            users = db.query(User).all()
            return users
    
    How it works:
    1. Creates a new session
    2. Yields it (gives it to your route)
    3. After route finishes, closes the session (cleanup)
    
    Why yield instead of return?
    - Ensures session is always closed (even if error occurs)
    - Like try/finally but cleaner
    """
    db = SessionLocal()
    try:
        yield db  # Give session to the route
    finally:
        db.close()  # Always close when done (prevents connection leaks)


# ===== Database Initialization =====

def init_db():
    """
    Initialize Database
    
    Creates all tables defined in models.
    Called once when app starts.
    
    Note: In production, use Alembic migrations instead.
    This is mainly for development/testing.
    """
    # Import all models here so Base knows about them
    # from app.models import user, hall, issue, category, audit_log
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def check_db_connection():
    """
    Check Database Connection
    
    Verifies we can connect to the database.
    Useful for health checks and startup validation.
    
    Returns:
        bool: True if connected, False otherwise
    """
    try:
        # Try to execute a simple query
        from sqlalchemy import text
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


# ===== Helper Functions =====

def get_db_url_safe():
    """
    Get Database URL (Safe for Logging)
    
    Returns database URL with password hidden.
    Useful for logging without exposing credentials.
    
    Example:
        postgresql://user:***@localhost:5432/dbname
    """
    url = settings.DATABASE_URL
    if "@" in url and ":" in url:
        # Hide password
        parts = url.split("@")
        credentials = parts[0].split(":")
        if len(credentials) >= 2:
            safe_url = f"{credentials[0]}:***@{parts[1]}"
            return safe_url
    return url

