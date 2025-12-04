"""
Admin Service

Business logic for admin management operations (DSA only).

This service handles:
- User management (create hall admin, reset passwords)
- Hall management (create halls with admin users)
- Category management (CRUD operations)

Why this service exists:
- Separates business logic from API routes
- Reusable functions for admin operations
- Easier to test (test logic without HTTP layer)
- Single Responsibility: Admin management business rules only
"""

import secrets
import string
import re
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from fastapi import HTTPException, status
from app.models import User, Hall, Category, Issue
from app.models.user import UserRole
from app.models.issue import IssueStatus
from app.utils.security import hash_password


def generate_secure_password(length: int = 12) -> str:
    """
    Generate a cryptographically secure random password.
    
    Uses secrets module (cryptographically secure random number generator)
    to generate passwords that are safe for production use.
    
    Args:
        length: Password length (default: 12 characters)
    
    Returns:
        str: Random password containing letters, digits, and symbols
    
    Example:
        password = generate_secure_password()
        # Returns: "aB3$kL9mN2pQ"
    """
    # Character set: letters (upper + lower), digits, basic symbols
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    
    # Use secrets.choice for cryptographically secure random selection
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    return password


def create_hall_admin_user(
    db: Session,
    hall_id: int,
    username: str,
    password: Optional[str] = None
) -> tuple[User, str]:
    """
    Create a hall admin user.
    
    Creates a new hall admin user with the specified hall association.
    If password is not provided, generates a secure random password.
    
    Args:
        db: Database session
        hall_id: ID of the hall this admin will manage
        username: Username for the hall admin (must be unique)
        password: Optional password (if None, generates random password)
    
    Returns:
        tuple: (User object, plain_text_password)
        - User: The created user object
        - plain_text_password: The password in plain text (for display to DSA)
    
    Raises:
        HTTPException 400: If username already exists
        HTTPException 404: If hall does not exist
    
    Example:
        user, password = create_hall_admin_user(
            db, hall_id=1, username="newhall"
        )
        # Returns: (User object, "aB3$kL9mN2pQ")
    """
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{username}' already exists"
        )
    
    # Verify hall exists
    hall = db.query(Hall).filter(Hall.id == hall_id).first()
    if not hall:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hall with ID {hall_id} not found"
        )
    
    # Generate password if not provided
    plain_text_password = password if password else generate_secure_password()
    
    # Hash password before storing
    password_hash = hash_password(plain_text_password)
    
    # Create user (no email)
    user = User(
        username=username,
        password_hash=password_hash,
        role=UserRole.HALL_ADMIN,
        hall_id=hall_id,
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user, plain_text_password


def reset_user_password(db: Session, user_id: int) -> str:
    """
    Reset a user's password to a new random password.
    
    Generates a new secure password and updates the user's password hash.
    Returns the plain text password for display to DSA.
    
    Args:
        db: Database session
        user_id: ID of the user whose password to reset
    
    Returns:
        str: The new password in plain text (for display to DSA)
    
    Raises:
        HTTPException 404: If user does not exist
    
    Example:
        new_password = reset_user_password(db, user_id=5)
        # Returns: "xK9$mP2nQ4rS"
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Generate new secure password
    new_password = generate_secure_password()
    
    # Hash and update password
    user.password_hash = hash_password(new_password)
    
    db.commit()
    
    return new_password


def create_hall_with_admin(
    db: Session,
    hall_name: str,
    password: Optional[str] = None,
    username: Optional[str] = None
) -> tuple[Hall, User, str]:
    """
    Create a new hall and its admin user in a single transaction.
    
    This ensures data integrity - if hall creation fails, user creation
    is rolled back, and vice versa.
    
    Username is auto-generated from hall_name (lowercase, no spaces) if not provided.
    
    Args:
        db: Database session
        hall_name: Name of the hall to create (must be unique)
        password: Optional password (if None, generates random password)
        username: Optional username (auto-generated from hall_name if not provided)
    
    Returns:
        tuple: (Hall object, User object, plain_text_password)
        - Hall: The created hall object
        - User: The created hall admin user
        - plain_text_password: The password in plain text (for display to DSA)
    
    Raises:
        HTTPException 400: If hall name or username already exists
    
    Example:
        hall, user, password = create_hall_with_admin(
            db, hall_name="New Hall"
        )
        # Username will be auto-generated as "newhall"
    """
    # Check if hall name already exists
    existing_hall = db.query(Hall).filter(Hall.name == hall_name).first()
    if existing_hall:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Hall '{hall_name}' already exists"
        )
    
    # Auto-generate username from hall_name if not provided
    if not username:
        # Convert to lowercase and remove spaces
        username = hall_name.lower().replace(" ", "").replace("-", "").replace("_", "")
        # Remove any special characters, keep only alphanumeric
        username = re.sub(r'[^a-z0-9]', '', username)
        if not username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not generate username from hall name. Please provide a username."
            )
    
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{username}' already exists. Please provide a different hall name or username."
        )
    
    # Generate password if not provided
    plain_text_password = password if password else generate_secure_password()
    
    # Hash password
    password_hash = hash_password(plain_text_password)
    
    try:
        # Create hall
        hall = Hall(name=hall_name)
        db.add(hall)
        db.flush()  # Get hall.id without committing
        
        # Create hall admin user (no email)
        user = User(
            username=username,
            password_hash=password_hash,
            role=UserRole.HALL_ADMIN,
            hall_id=hall.id,
            is_active=True
        )
        db.add(user)
        
        # Commit transaction (both hall and user created together)
        db.commit()
        
        # Refresh to get database-generated fields
        db.refresh(hall)
        db.refresh(user)
        
        return hall, user, plain_text_password
    
    except Exception as e:
        # Rollback on any error
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create hall and admin: {str(e)}"
        )


def get_all_users_with_stats(db: Session) -> List[Dict[str, Any]]:
    """
    Get all users with their hall information.
    
    Returns a list of users with their associated hall names
    and basic statistics, including account lockout status.
    
    Args:
        db: Database session
    
    Returns:
        List of dictionaries containing user information
    
    Example:
        users = get_all_users_with_stats(db)
        # Returns: [
        #     {"id": 1, "username": "levi", "role": "hall_admin", "hall_name": "Levi", "is_locked": False, ...},
        #     {"id": 2, "username": "dsa", "role": "admin", "hall_name": None, "is_locked": True, ...}
        # ]
    """
    users = db.query(User).order_by(User.created_at.desc()).all()
    
    result = []
    for user in users:
        user_dict = {
            "id": user.id,
            "username": user.username,
            "role": user.role.value,
            "hall_id": user.hall_id,
            "hall_name": user.hall.name if user.hall else None,
            "is_active": user.is_active,
            "has_security_question": bool(user.security_question),
            "is_locked": user.is_locked,  # Account lockout status
            "lockout_remaining_minutes": user.lockout_remaining_minutes,  # Minutes until unlock
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
        result.append(user_dict)
    
    return result


def get_all_halls_with_stats(db: Session) -> List[Dict[str, Any]]:
    """
    Get all halls with issue statistics.
    
    Returns a list of halls with counts of total, pending, in_progress,
    and done issues for each hall.
    
    Args:
        db: Database session
    
    Returns:
        List of dictionaries containing hall information with stats
    
    Example:
        halls = get_all_halls_with_stats(db)
        # Returns: [
        #     {"id": 1, "name": "Levi", "total": 45, "pending": 5, "in_progress": 3, "done": 37, ...},
        #     ...
        # ]
    """
    # Query halls with issue counts grouped by status
    halls_query = (
        db.query(
            Hall.id,
            Hall.name,
            Hall.created_at,
            func.count(Issue.id).label("total"),
            func.sum(
                case((Issue.status == IssueStatus.PENDING, 1), else_=0)
            ).label("pending"),
            func.sum(
                case((Issue.status == IssueStatus.IN_PROGRESS, 1), else_=0)
            ).label("in_progress"),
            func.sum(
                case((Issue.status == IssueStatus.DONE, 1), else_=0)
            ).label("done"),
        )
        .outerjoin(Issue, Hall.id == Issue.hall_id)
        .group_by(Hall.id, Hall.name, Hall.created_at)
        .order_by(Hall.name)
    )
    
    results = halls_query.all()
    
    halls_list = []
    for row in results:
        halls_list.append({
            "id": row.id,
            "name": row.name,
            "total": row.total or 0,
            "pending": int(row.pending or 0),
            "in_progress": int(row.in_progress or 0),
            "done": int(row.done or 0),
            "created_at": row.created_at.isoformat() if row.created_at else None,
        })
    
    return halls_list


def create_category(db: Session, name: str) -> Category:
    """
    Create a new issue category.
    
    Args:
        db: Database session
        name: Category name (must be unique)
    
    Returns:
        Category: The created category object
    
    Raises:
        HTTPException 400: If category name already exists
    
    Example:
        category = create_category(db, name="New Category")
    """
    # Check if category already exists
    existing = db.query(Category).filter(Category.name == name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category '{name}' already exists"
        )
    
    category = Category(name=name, is_active=True)
    db.add(category)
    db.commit()
    db.refresh(category)
    
    return category


def update_category(db: Session, category_id: int, name: str) -> Category:
    """
    Update a category's name.
    
    Args:
        db: Database session
        category_id: ID of the category to update
        name: New category name (must be unique)
    
    Returns:
        Category: The updated category object
    
    Raises:
        HTTPException 404: If category does not exist
        HTTPException 400: If new name already exists
    
    Example:
        category = update_category(db, category_id=5, name="Updated Name")
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found"
        )
    
    # Check if new name already exists (excluding current category)
    existing = db.query(Category).filter(
        Category.name == name,
        Category.id != category_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category '{name}' already exists"
        )
    
    category.name = name
    db.commit()
    db.refresh(category)
    
    return category


def soft_delete_category(db: Session, category_id: int) -> Category:
    """
    Soft delete a category by setting is_active to False.
    
    This preserves historical data while hiding the category from
    active use (dropdowns, forms, etc.).
    
    Args:
        db: Database session
        category_id: ID of the category to soft delete
    
    Returns:
        Category: The updated category object (with is_active=False)
    
    Raises:
        HTTPException 404: If category does not exist
    
    Example:
        category = soft_delete_category(db, category_id=5)
        # category.is_active is now False
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found"
        )
    
    category.is_active = False
    db.commit()
    db.refresh(category)
    
    return category


def reactivate_category(db: Session, category_id: int) -> Category:
    """
    Reactivate a previously soft-deleted category.
    
    Sets is_active=True so the category appears in dropdowns/forms again.
    
    Args:
        db: Database session
        category_id: ID of the category to reactivate
    
    Returns:
        Category: The updated category object (with is_active=True)
    
    Raises:
        HTTPException 404: If category does not exist
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found"
        )
    
    if not category.is_active:
        category.is_active = True
        db.commit()
        db.refresh(category)
    
    return category


def get_all_categories(db: Session) -> List[Dict[str, Any]]:
    """
    Get all categories (active and inactive).
    
    Args:
        db: Database session
    
    Returns:
        List of dictionaries containing category information
    
    Example:
        categories = get_all_categories(db)
        # Returns: [
        #     {"id": 1, "name": "Plumbing", "is_active": True, ...},
        #     {"id": 2, "name": "Old Category", "is_active": False, ...}
        # ]
    """
    categories = db.query(Category).order_by(
        Category.is_active.desc(),  # Active first
        Category.name
    ).all()
    
    result = []
    for category in categories:
        result.append({
            "id": category.id,
            "name": category.name,
            "is_active": category.is_active,
            "created_at": category.created_at.isoformat() if category.created_at else None,
        })
    
    return result


# ===== Account Lockout Management =====

def unlock_user(db: Session, user_id: int) -> User:
    """
    Unlock a user's account by clearing failed login attempts and lockout time.
    
    This function:
    1. Resets failed_login_attempts to 0
    2. Clears locked_until timestamp
    
    Called by:
    - DSA manually unlocking a user via /api/admin/users/{id}/unlock
    - password_service when security question recovery succeeds
    
    Args:
        db: Database session
        user_id: ID of the user to unlock
    
    Returns:
        User: The unlocked user object
    
    Raises:
        HTTPException 404: If user does not exist
    
    Example:
        user = unlock_user(db, user_id=5)
        # User's failed_login_attempts = 0, locked_until = None
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Clear lockout
    user.failed_login_attempts = 0
    user.locked_until = None
    
    db.commit()
    db.refresh(user)
    
    return user

