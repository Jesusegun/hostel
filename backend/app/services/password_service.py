"""
Password Service

Business logic for password recovery using security questions.

This service handles:
- Setting security questions (DSA only)
- Verifying security answers
- Resetting passwords with security questions

Why this service exists:
- Separates password recovery logic from API routes
- Reusable functions for password operations
- Easier to test (test logic without HTTP layer)
- Single Responsibility: Password recovery business rules only
"""

from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models import User
from app.utils.security import hash_password, verify_password


def set_security_question(
    db: Session,
    user_id: int,
    question: str,
    answer: str
) -> User:
    """
    Set or update a user's security question and answer.
    
    The security answer is hashed (like passwords) before storing.
    Only DSA should have security questions set.
    
    Args:
        db: Database session
        user_id: ID of the user to set security question for
        question: Security question text
        answer: Security answer (will be hashed before storing)
    
    Returns:
        User: The updated user object
    
    Raises:
        HTTPException 404: If user does not exist
        HTTPException 400: If question or answer is empty
    
    Example:
        user = set_security_question(
            db, user_id=1, question="What city were you born in?", answer="Lagos"
        )
    """
    # Validate inputs
    if not question or not question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security question cannot be empty"
        )
    
    if not answer or not answer.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security answer cannot be empty"
        )
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Hash the security answer (treat it like a password)
    answer_hash = hash_password(answer.strip())
    
    # Update user
    user.security_question = question.strip()
    user.security_answer_hash = answer_hash
    
    db.commit()
    db.refresh(user)
    
    return user


def verify_security_answer(
    db: Session,
    username: str,
    answer: str
) -> bool:
    """
    Verify a security answer for a user.
    
    Compares the provided answer against the stored hashed answer.
    Uses constant-time comparison to prevent timing attacks.
    
    Args:
        db: Database session
        username: Username of the user
        answer: Security answer to verify
    
    Returns:
        bool: True if answer is correct, False otherwise
    
    Raises:
        HTTPException 404: If user does not exist
        HTTPException 400: If user has no security question set
    
    Example:
        is_correct = verify_security_answer(db, username="dsa", answer="Lagos")
        # Returns: True or False
    """
    # Get user
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )
    
    # Check if security question is set
    if not user.security_question or not user.security_answer_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security question not set for this user"
        )
    
    # Verify answer using same function as password verification
    return verify_password(answer.strip(), user.security_answer_hash)


def reset_password_with_security_question(
    db: Session,
    username: str,
    answer: str,
    new_password: str
) -> User:
    """
    Reset a user's password after verifying their security answer.
    
    This is the complete flow for password recovery:
    1. Verify the security answer
    2. If correct, update the password
    3. Clear any account lockout (so DSA can recover if locked out)
    4. Return the updated user
    
    Args:
        db: Database session
        username: Username of the user
        answer: Security answer to verify
        new_password: New password to set (will be hashed)
    
    Returns:
        User: The updated user object
    
    Raises:
        HTTPException 404: If user does not exist
        HTTPException 400: If security question not set or answer is incorrect
        HTTPException 400: If new password is too short
    
    Example:
        user = reset_password_with_security_question(
            db, username="dsa", answer="Lagos", new_password="newpass123"
        )
    """
    # Validate new password
    if not new_password or len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    # Get user
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )
    
    # Check if security question is set
    if not user.security_question or not user.security_answer_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security question not set for this user"
        )
    
    # Verify security answer
    if not verify_password(answer.strip(), user.security_answer_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect security answer"
        )
    
    # Hash and update password
    user.password_hash = hash_password(new_password)
    
    # Clear any account lockout (DSA self-recovery clears lockout)
    # This allows DSA to recover even if their account was locked
    user.failed_login_attempts = 0
    user.locked_until = None
    
    db.commit()
    db.refresh(user)
    
    return user


def get_security_question(db: Session, username: str) -> Optional[str]:
    """
    Get the security question for a user (without the answer).
    
    This is used in the forgot password flow - user enters username,
    system shows the security question, user enters answer.
    
    Args:
        db: Database session
        username: Username of the user
    
    Returns:
        str: Security question if set, None otherwise
    
    Raises:
        HTTPException 404: If user does not exist
    
    Example:
        question = get_security_question(db, username="dsa")
        # Returns: "What city were you born in?" or None
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )
    
    return user.security_question if user.security_question else None

