"""
Authentication Service

Business logic for user authentication.

This service handles:
- User lookup by username
- Password verification
- User status validation (active/inactive)
- Account lockout (5 failed attempts = 45 minute lockout)

Why this service exists:
- Separates authentication logic from API routes
- Reusable (can be called from multiple endpoints)
- Easier to test (test logic without HTTP layer)
- Single Responsibility: Authentication business rules only
"""

from typing import Optional, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models import User
from app.models.user import UserRole
from app.utils.security import verify_password

# Account lockout configuration
MAX_FAILED_ATTEMPTS = 5  # Lock account after 5 failed attempts
LOCKOUT_DURATION_MINUTES = 45  # Lock for 45 minutes


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    Get a user by username from the database.
    
    Args:
        db: Database session
        username: Username to search for
    
    Returns:
        User object if found, None otherwise
    
    Example:
        user = get_user_by_username(db, "levi")
        if user:
            print(user.role)  # "hall_admin"
    """
    return db.query(User).filter(User.username == username).first()


def authenticate_user(db: Session, username: str, password: str) -> Tuple[Optional[User], Optional[str]]:
    """
    Authenticate a user by username and password.
    
    This function:
    1. Looks up user by username
    2. Checks if account is locked (returns error with remaining time)
    3. Checks if user exists and is active
    4. Verifies password against stored hash
    5. If password wrong, increments failed attempts (locks after 5 failures)
    6. If password correct, resets failed attempts
    7. Returns User object if authentication succeeds
    
    Args:
        db: Database session
        username: Username to authenticate
        password: Plain text password to verify
    
    Returns:
        Tuple of (User, error_message):
        - (User, None) if authentication succeeds
        - (None, "error message") if authentication fails
        - (None, "locked:XX") if account is locked (XX = minutes remaining)
    
    Security Notes:
        - Returns generic error for invalid credentials (doesn't reveal if username exists)
        - Uses constant-time password comparison (bcrypt)
        - Checks user.is_active before allowing login
        - Implements account lockout after 5 failed attempts
    
    Example:
        user, error = authenticate_user(db, "levi", "changeme123")
        if user:
            print(f"Authenticated: {user.username}")
        elif error and error.startswith("locked:"):
            minutes = error.split(":")[1]
            print(f"Account locked for {minutes} more minutes")
        else:
            print("Invalid credentials")
    
    Edge Cases Handled:
        - User doesn't exist: Returns (None, "invalid")
        - User is inactive: Returns (None, "invalid")
        - Account is locked: Returns (None, "locked:XX")
        - Wrong password: Increments counter, returns (None, "invalid")
        - Empty username/password: Returns (None, "invalid") (handled by Pydantic validation)
    """
    # Get user from database
    user = get_user_by_username(db, username)
    
    # If user doesn't exist, return generic error
    # (Don't reveal that username doesn't exist - security best practice)
    if not user:
        return None, "invalid"
    
    # Check if account is locked
    if user.is_locked:
        return None, f"locked:{user.lockout_remaining_minutes}"
    
    # Check if user account is active
    if not user.is_active:
        return None, "invalid"
    
    # Verify password
    if not verify_password(password, user.password_hash):
        # Wrong password - increment failed attempts
        _increment_failed_attempts(db, user)
        
        # Check if now locked (after incrementing)
        if user.is_locked:
            return None, f"locked:{user.lockout_remaining_minutes}"
        
        return None, "invalid"
    
    # Authentication successful - reset failed attempts
    _reset_failed_attempts(db, user)
    
    return user, None


def _increment_failed_attempts(db: Session, user: User) -> None:
    """
    Increment failed login attempts for a user.
    
    If attempts reach MAX_FAILED_ATTEMPTS, lock the account.
    
    Args:
        db: Database session
        user: User to increment attempts for
    """
    user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
    
    # Lock account if max attempts reached
    if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
    
    db.commit()


def _reset_failed_attempts(db: Session, user: User) -> None:
    """
    Reset failed login attempts for a user after successful login.
    
    Args:
        db: Database session
        user: User to reset attempts for
    """
    if user.failed_login_attempts > 0 or user.locked_until is not None:
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()

