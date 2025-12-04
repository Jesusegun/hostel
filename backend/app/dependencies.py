"""
FastAPI Dependencies

Reusable dependencies for route protection and user authentication.

Why Dependencies:
- DRY: Don't repeat authentication logic in every route
- Automatic: FastAPI handles dependency injection
- Testable: Easy to mock dependencies for testing
- Clean: Routes focus on business logic, not authentication

Usage:
    @app.get("/protected")
    def protected_route(current_user: User = Depends(get_current_user)):
        return {"message": f"Hello {current_user.username}"}
"""

from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError
from app.database import get_db
from app.models import User
from app.models.user import UserRole
from app.schemas.auth import TokenData
from app.utils.security import decode_access_token
from app.services.auth_service import get_user_by_username


# OAuth2 scheme for token extraction
# This tells FastAPI to look for Bearer token in Authorization header
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    scheme_name="JWT"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    This dependency:
    1. Extracts JWT token from Authorization header
    2. Decodes and validates token
    3. Looks up user in database
    4. Returns User object
    
    Args:
        token: JWT token (automatically extracted by OAuth2PasswordBearer)
        db: Database session (automatically injected)
    
    Returns:
        User: Current authenticated user
    
    Raises:
        HTTPException 401: If token is invalid, expired, or user not found
    
    Usage:
        @app.get("/api/issues")
        def get_issues(current_user: User = Depends(get_current_user)):
            # current_user is guaranteed to be authenticated
            return {"user": current_user.username}
    
    Security Notes:
        - Validates token signature (prevents tampering)
        - Checks token expiration
        - Verifies user still exists in database
        - Checks user is active
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode token
        payload = decode_access_token(token)
        
        # Extract username from token (sub = subject = username)
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        # Extract role and hall_id from token
        role: Optional[str] = payload.get("role")
        hall_id: Optional[int] = payload.get("hall_id")
        
        # Create token data object
        token_data = TokenData(
            username=username,
            role=role,
            hall_id=hall_id
        )
    except JWTError:
        # Token is invalid or expired
        raise credentials_exception
    
    # Get user from database
    user = get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    
    # Check if user is still active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


def require_role(allowed_roles: List[UserRole]):
    """
    Dependency factory for role-based access control.
    
    Creates a dependency that checks if the current user has one of the allowed roles.
    
    Args:
        allowed_roles: List of UserRole enums that are allowed to access the route
    
    Returns:
        Dependency function that raises 403 if user role is not allowed
    
    Usage:
        @app.get("/api/admin/users")
        def get_users(
            current_user: User = Depends(require_role([UserRole.ADMIN]))
        ):
            # Only admin users can access this
            return {"users": [...]}
    
    Example:
        # Allow both hall_admin and admin
        Depends(require_role([UserRole.HALL_ADMIN, UserRole.ADMIN]))
        
        # Only admin
        Depends(require_role([UserRole.ADMIN]))
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        # Check if user's role is in allowed roles
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {[r.value for r in allowed_roles]}"
            )
        return current_user
    
    return role_checker


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency for admin-only routes.
    
    Shortcut for require_role([UserRole.ADMIN]).
    
    Usage:
        @app.post("/api/admin/halls")
        def create_hall(current_user: User = Depends(require_admin)):
            # Only admin users can access this
            return {"message": "Hall created"}
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin role required."
        )
    return current_user


def require_hall_admin_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency for routes accessible by both hall admins and admin users.
    
    Usage:
        @app.get("/api/issues")
        def get_issues(current_user: User = Depends(require_hall_admin_or_admin)):
            # Both hall admins and admins can access this
            return {"issues": [...]}
    """
    # Both roles are allowed, so just return the user
    # (get_current_user already ensures user is authenticated)
    return current_user


def require_dsa(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency for DSA-only routes (admin management features).
    
    Only the 'dsa' username can access these endpoints.
    maintenance_officer cannot access admin management.
    
    Usage:
        @router.post("/api/admin/users")
        def create_user(current_user: User = Depends(require_dsa)):
            # Only DSA can access this
            return {"message": "User created"}
    
    Raises:
        HTTPException 403: If user is not DSA
    """
    if current_user.username != "dsa":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. DSA role required for admin management."
        )
    return current_user

