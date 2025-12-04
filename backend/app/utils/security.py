"""
Security Utilities

This module provides password hashing and JWT token generation/validation functions.

Why these functions exist:
- Password hashing: Never store plain text passwords (security requirement)
- JWT tokens: Stateless authentication (no server-side session storage needed)
- Token validation: Verify user identity on every request

Security Best Practices:
- Use bcrypt for password hashing (cost factor 12 = ~300ms hash time)
- JWT tokens expire after 24 hours (forces periodic re-authentication)
- Token payload contains minimal data (username, role, hall_id only)
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import bcrypt
from jose import JWTError, jwt
from app.config import settings


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Uses cost factor 12, which provides good security while maintaining
    reasonable performance (~300ms hash time).
    
    Args:
        password: Plain text password to hash
    
    Returns:
        str: Bcrypt hashed password (starts with $2b$12$...)
    
    Example:
        hashed = hash_password("mypassword123")
        # Returns: "$2b$12$eHkcn3gLT6K23P5ZGUgTOO2Tbm2esKAxiwNoeyiZ6s43DeNp9MmcW"
    """
    # Convert password to bytes
    password_bytes = password.encode('utf-8')
    
    # Ensure password is within bcrypt's 72-byte limit
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # Generate salt and hash password
    salt = bcrypt.gensalt(rounds=12)  # Cost factor 12
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Return as string (bcrypt hash is ASCII-safe)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a bcrypt hash.
    
    Uses constant-time comparison to prevent timing attacks.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hashed password from database
    
    Returns:
        bool: True if password matches, False otherwise
    
    Example:
        is_valid = verify_password("mypassword123", "$2b$12$...")
        # Returns: True or False
    """
    try:
        # Convert to bytes
        password_bytes = plain_password.encode('utf-8')
        
        # Ensure password is within bcrypt's 72-byte limit
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        hashed_bytes = hashed_password.encode('utf-8')
        
        # Use bcrypt.checkpw for constant-time comparison
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        # If any error occurs (invalid hash format, etc.), return False
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    The token contains user information (username, role, hall_id) and expires
    after the specified time (default: 24 hours from config).
    
    Args:
        data: Dictionary containing user data to encode in token
            Should include: username, role, hall_id (optional)
        expires_delta: Optional custom expiration time. If None, uses
            settings.JWT_EXPIRATION_HOURS
    
    Returns:
        str: JWT token string
    
    Example:
        token = create_access_token({
            "sub": "levi",
            "role": "hall_admin",
            "hall_id": 1
        })
        # Returns: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    
    Security Notes:
        - Token is signed with JWT_SECRET_KEY (never expose this!)
        - Token expires automatically (prevents indefinite access)
        - Payload contains minimal data (no sensitive information)
    """
    # Create a copy of data to avoid modifying the original
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Use expiration hours from config (default: 24 hours)
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    # Add expiration to token payload
    to_encode.update({"exp": expire})
    
    # Add issued at time (iat) for token freshness tracking
    to_encode.update({"iat": datetime.utcnow()})
    
    # Encode token with secret key and algorithm
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT access token.
    
    Verifies:
    - Token signature (not tampered with)
    - Token expiration (not expired)
    - Token format (valid JWT structure)
    
    Args:
        token: JWT token string to decode
    
    Returns:
        dict: Decoded token payload (contains user data)
    
    Raises:
        JWTError: If token is invalid, expired, or tampered with
    
    Example:
        payload = decode_access_token("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
        # Returns: {"sub": "levi", "role": "hall_admin", "hall_id": 1, "exp": 1234567890}
    
    Security Notes:
        - Always validates signature (prevents token tampering)
        - Checks expiration automatically (raises JWTError if expired)
        - Never trust client data - always validate server-side
    """
    try:
        # Decode and verify token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        # Token has expired
        raise JWTError("Token has expired")
    except jwt.JWTError as e:
        # Token is invalid (wrong signature, malformed, etc.)
        raise JWTError(f"Invalid token: {str(e)}")

