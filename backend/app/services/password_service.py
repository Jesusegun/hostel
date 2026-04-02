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
from datetime import datetime, timedelta, timezone
import hashlib
import secrets
import logging
from collections import defaultdict
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models import User, PasswordResetAuditLog
from app.utils.security import hash_password, verify_password
from app.config import settings
from app.services.email_service import send_password_reset_email


logger = logging.getLogger(__name__)
_request_ip_timestamps = defaultdict(list)


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


def change_password_authenticated(
    db: Session,
    user: User,
    current_password: str,
    new_password: str,
    confirm_password: str
) -> User:
    """
    Change password for an authenticated user.

    This flow verifies the current password before changing to a new one.

    Args:
        db: Database session
        user: Current authenticated user
        current_password: User's existing password
        new_password: New password to set
        confirm_password: Confirmation for the new password

    Returns:
        User: Updated user object

    Raises:
        HTTPException 400: For invalid input or password mismatch
        HTTPException 401: If current password is incorrect
    """
    if not current_password or not current_password.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is required"
        )

    if not new_password or len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long"
        )

    if new_password != confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirmation do not match"
        )

    if current_password == new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )

    if not verify_password(current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )

    user.password_hash = hash_password(new_password)
    user.failed_login_attempts = 0
    user.locked_until = None

    db.commit()
    db.refresh(user)

    return user


def _log_reset_event(
    db: Session,
    *,
    action: str,
    success: bool,
    user: Optional[User] = None,
    identifier_input: Optional[str] = None,
    request_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    reason: Optional[str] = None,
) -> None:
    """Persist a password-reset audit event with best-effort safety."""
    try:
        event = PasswordResetAuditLog(
            user_id=user.id if user else None,
            action=action,
            success=success,
            identifier_input=identifier_input,
            request_ip=request_ip,
            user_agent=(user_agent or "")[:255] or None,
            reason=reason,
        )
        db.add(event)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("Failed to write password reset audit log: %s", exc)


def _enforce_reset_request_ip_rate_limit(request_ip: Optional[str]) -> None:
    """Apply in-memory IP rate limiting for forgot-password requests."""
    if not request_ip:
        return

    now = datetime.now(timezone.utc)
    window_seconds = settings.PASSWORD_RESET_RATE_LIMIT_WINDOW_SECONDS
    max_requests = settings.PASSWORD_RESET_MAX_REQUESTS_PER_WINDOW
    cutoff = now - timedelta(seconds=window_seconds)

    timestamps = [ts for ts in _request_ip_timestamps[request_ip] if ts > cutoff]
    _request_ip_timestamps[request_ip] = timestamps

    if len(timestamps) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many reset requests. Please try again later."
        )

    _request_ip_timestamps[request_ip].append(now)


def request_password_reset_email(
    db: Session,
    identifier: str,
    request_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """
    Request a one-time password reset link via email.

    Accepts username or email as identifier. For security, callers should
    always return a generic success response regardless of user existence.
    """
    if not identifier or not identifier.strip():
        return

    _enforce_reset_request_ip_rate_limit(request_ip)

    normalized = identifier.strip().lower()
    now = datetime.now(timezone.utc)

    user = db.query(User).filter(
        or_(
            func.lower(User.username) == normalized,
            func.lower(User.email) == normalized,
        )
    ).first()

    if not user or not user.is_active or not user.email:
        _log_reset_event(
            db,
            action="request",
            success=True,
            identifier_input=normalized,
            request_ip=request_ip,
            user_agent=user_agent,
            reason="generic_response",
        )
        return

    cooldown_seconds = settings.PASSWORD_RESET_REQUEST_COOLDOWN_SECONDS
    if user.password_reset_requested_at:
        elapsed = (now - user.password_reset_requested_at).total_seconds()
        if elapsed < cooldown_seconds:
            _log_reset_event(
                db,
                action="request_blocked",
                success=False,
                user=user,
                identifier_input=normalized,
                request_ip=request_ip,
                user_agent=user_agent,
                reason="cooldown_active",
            )
            return

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    user.password_reset_token_hash = token_hash
    user.password_reset_token_expires_at = now + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRY_MINUTES)
    user.password_reset_requested_at = now
    user.password_reset_used_at = None

    db.commit()

    _log_reset_event(
        db,
        action="request",
        success=True,
        user=user,
        identifier_input=normalized,
        request_ip=request_ip,
        user_agent=user_agent,
    )

    try:
        send_password_reset_email(
            recipient_email=user.email,
            reset_token=raw_token,
            username=user.username,
        )
    except Exception as exc:
        logger.error("Password reset email dispatch failed for user %s: %s", user.username, exc)


def reset_password_with_token(
    db: Session,
    token: str,
    new_password: str,
    confirm_password: str,
) -> User:
    """
    Reset password using a valid one-time token.
    """
    if not token or not token.strip():
        _log_reset_event(
            db,
            action="reset_failure",
            success=False,
            reason="missing_token",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    if not new_password or len(new_password) < 8:
        _log_reset_event(
            db,
            action="reset_failure",
            success=False,
            reason="weak_password",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )

    if new_password != confirm_password:
        _log_reset_event(
            db,
            action="reset_failure",
            success=False,
            reason="password_mismatch",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirmation do not match"
        )

    token_hash = hashlib.sha256(token.strip().encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc)

    user = db.query(User).filter(
        User.password_reset_token_hash == token_hash,
        User.password_reset_token_expires_at.isnot(None),
        User.password_reset_token_expires_at > now,
        User.password_reset_used_at.is_(None),
        User.is_active.is_(True),
    ).first()

    if not user:
        _log_reset_event(
            db,
            action="reset_failure",
            success=False,
            reason="invalid_or_expired_token",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    if verify_password(new_password, user.password_hash):
        _log_reset_event(
            db,
            action="reset_failure",
            success=False,
            user=user,
            reason="password_reuse",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )

    user.password_hash = hash_password(new_password)
    user.failed_login_attempts = 0
    user.locked_until = None
    user.password_reset_used_at = now
    user.password_reset_token_hash = None
    user.password_reset_token_expires_at = None

    db.commit()
    db.refresh(user)

    _log_reset_event(
        db,
        action="reset_success",
        success=True,
        user=user,
    )

    return user

