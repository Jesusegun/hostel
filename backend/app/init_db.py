"""
Database Initialization Script

This script creates all database tables and optionally seeds initial data.

Usage:
    python -m app.init_db

What it does:
1. Creates all tables (halls, categories, users, issues, audit_logs)
2. Seeds initial data (11 halls, 10 categories, 13 users)

Why we need this:
- PostgreSQL needs to know the table structure before storing data
- We need initial data (halls, categories, users) to start using the system
- This is a one-time setup (run once when deploying)
"""

from sqlalchemy.orm import Session
import bcrypt
from app.database import engine, SessionLocal, Base
from app.models import Hall, Category, User, Issue, AuditLog
from app.models.user import UserRole
import sys


def create_tables():
    """
    Create all database tables
    
    This reads the SQLAlchemy models and creates corresponding tables in PostgreSQL.
    If tables already exist, this does nothing (safe to run multiple times).
    """
    print("=" * 60)
    print("Creating database tables...")
    print("=" * 60)
    
    try:
        # Create all tables defined in Base.metadata
        Base.metadata.create_all(bind=engine)
        print("SUCCESS: All tables created successfully!")
        return True
    except Exception as e:
        print(f"ERROR: Failed to create tables: {e}")
        return False


def seed_halls(db: Session):
    """
    Seed initial halls (hostels)
    
    Creates the 11 university halls if they don't exist.
    """
    print("\nSeeding halls...")
    
    hall_names = [
        "Levi", "Integrity", "Joseph", "Joshua", "Elisha",
        "Deborah", "Mercy", "Mary", "Esme", "Sussana", "Rebecca"
    ]
    
    created_count = 0
    for hall_name in hall_names:
        # Check if hall already exists
        existing_hall = db.query(Hall).filter(Hall.name == hall_name).first()
        if not existing_hall:
            hall = Hall(name=hall_name)
            db.add(hall)
            created_count += 1
            print(f"  - Created hall: {hall_name}")
        else:
            print(f"  - Hall already exists: {hall_name}")
    
    db.commit()
    print(f"SUCCESS: {created_count} new halls created, {len(hall_names) - created_count} already existed")


def seed_categories(db: Session):
    """
    Seed initial issue categories
    
    Creates the 10 issue categories from the Google Form.
    """
    print("\nSeeding categories...")
    
    category_names = [
        "Plumbing",
        "Carpentry",
        "Electrical Issues",
        "Door Issues",
        "Bathroom/Toilet",
        "Window",
        "Wardrobe",
        "Bunk",
        "Fan",
        "Others"
    ]
    
    created_count = 0
    for category_name in category_names:
        # Check if category already exists
        existing_category = db.query(Category).filter(Category.name == category_name).first()
        if not existing_category:
            category = Category(name=category_name, is_active=True)
            db.add(category)
            created_count += 1
            print(f"  - Created category: {category_name}")
        else:
            print(f"  - Category already exists: {category_name}")
    
    db.commit()
    print(f"SUCCESS: {created_count} new categories created, {len(category_names) - created_count} already existed")


def seed_users(db: Session):
    """
    Seed initial users (hall admins and admin users)
    
    Creates:
    - 11 hall admin users (one for each hall)
    - 2 admin users (maintenance_officer, dsa)
    
    Default password for all users: "changeme123"
    IMPORTANT: Users should change their password on first login!
    """
    print("\nSeeding users...")
    
    default_password = "changeme123"
    # Hash password with bcrypt directly
    password_bytes = default_password.encode('utf-8')
    # Ensure password is within bcrypt's 72-byte limit
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    
    created_count = 0
    
    # Create hall admin users
    print("\n  Creating hall admin users...")
    halls = db.query(Hall).all()
    for hall in halls:
        username = hall.name.lower()  # e.g., "levi", "integrity"
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if not existing_user:
            user = User(
                username=username,
                password_hash=password_hash,
                role=UserRole.HALL_ADMIN,
                hall_id=hall.id,
                is_active=True
            )
            db.add(user)
            created_count += 1
            print(f"    - Created hall admin: {username} (Hall: {hall.name})")
        else:
            print(f"    - Hall admin already exists: {username}")
    
    # Create admin users
    print("\n  Creating admin users...")
    admin_usernames = ["maintenance_officer", "dsa"]
    for username in admin_usernames:
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if not existing_user:
            user = User(
                username=username,
                password_hash=password_hash,
                role=UserRole.ADMIN,
                hall_id=None,  # Admin users don't belong to a specific hall
                is_active=True
            )
            db.add(user)
            created_count += 1
            print(f"    - Created admin user: {username}")
        else:
            print(f"    - Admin user already exists: {username}")
    
    db.commit()
    print(f"\nSUCCESS: {created_count} new users created")
    print(f"DEFAULT PASSWORD FOR ALL USERS: {default_password}")
    print("IMPORTANT: Users should change their password on first login!")


def initialize_database():
    """
    Main function to initialize the database
    
    Steps:
    1. Create all tables
    2. Seed halls
    3. Seed categories
    4. Seed users
    """
    print("\n" + "=" * 60)
    print("DATABASE INITIALIZATION")
    print("=" * 60)
    
    # Step 1: Create tables
    if not create_tables():
        print("\nERROR: Failed to create tables. Exiting.")
        sys.exit(1)
    
    # Step 2: Seed data
    db = SessionLocal()
    try:
        seed_halls(db)
        seed_categories(db)
        seed_users(db)
        
        print("\n" + "=" * 60)
        print("DATABASE INITIALIZATION COMPLETE!")
        print("=" * 60)
        print("\nYou can now:")
        print("  1. Start the FastAPI server: uvicorn app.main:app --reload")
        print("  2. Login with any hall admin (e.g., username: 'levi', password: 'changeme123')")
        print("  3. Or login as admin (username: 'maintenance_officer', password: 'changeme123')")
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\nERROR: Failed to seed data: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    initialize_database()

