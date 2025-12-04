"""
Authentication API Routes

Handles user authentication endpoints:
- POST /api/auth/login - User login
- GET /api/auth/me - Get current user info
- POST /api/auth/logout - User logout (client-side)

Why these endpoints exist:
- Login: Authenticate users and issue JWT tokens
- Me: Verify token and get current user info
- Logout: Client-side token removal (JWT is stateless)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas.auth import LoginRequest, LoginResponse, UserResponse
from app.schemas.admin import (
    SetSecurityQuestionRequest,
    ForgotPasswordRequest,
    SecurityQuestionResponse,
    VerifySecurityAnswerRequest,
)
from app.services.auth_service import authenticate_user
from app.services.password_service import (
    set_security_question,
    get_security_question,
    reset_password_with_security_question,
)
from app.utils.security import create_access_token
from app.dependencies import get_current_user, require_dsa

# Create router for authentication endpoints
router = APIRouter()


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    User login endpoint.
    
    Authenticates user with username and password, returns JWT token.
    
    Args:
        form_data: OAuth2PasswordRequestForm (username and password)
        db: Database session
    
    Returns:
        LoginResponse: JWT token and user information
    
    Raises:
        HTTPException 401: If credentials are invalid
    
    Example Request:
        POST /api/auth/login
        Content-Type: application/x-www-form-urlencoded
        
        username=levi&password=changeme123
    
    Example Response:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "user": {
                "id": 1,
                "username": "levi",
                "role": "hall_admin",
                "hall_id": 1,
                "hall_name": "Levi",
                "is_active": true
            }
        }
    
    Security Notes:
        - Uses OAuth2PasswordRequestForm for standard OAuth2 compatibility
        - Returns generic error for invalid credentials (prevents username enumeration)
        - Token expires after 24 hours (from config)
        - Account lockout: After 5 failed attempts, account is locked for 45 minutes
    """
    # Authenticate user (now returns tuple: user, error_message)
    user, error = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        # Check if account is locked
        if error and error.startswith("locked:"):
            minutes = error.split(":")[1]
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account is locked. Try again in {minutes} minutes.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Generic error message (don't reveal if username exists)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Prepare token data
    token_data = {
        "sub": user.username,  # Subject (username)
        "role": user.role.value,  # User role
    }
    
    # Add hall_id to token if user is hall admin
    if user.hall_id:
        token_data["hall_id"] = user.hall_id
    
    # Create access token
    access_token = create_access_token(data=token_data)
    
    # Build user response
    user_response = UserResponse(
        id=user.id,
        username=user.username,
        role=user.role.value,
        hall_id=user.hall_id,
        hall_name=user.hall.name if user.hall else None,
        is_active=user.is_active,
    )
    
    # Return token and user info
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information.
    
    Returns user information for the currently authenticated user
    (determined by JWT token in Authorization header).
    
    Args:
        current_user: Current authenticated user (from JWT token)
    
    Returns:
        UserResponse: Current user information
    
    Raises:
        HTTPException 401: If token is invalid or expired
    
    Example Request:
        GET /api/auth/me
        Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    
    Example Response:
        {
            "id": 1,
            "username": "levi",
            "role": "hall_admin",
            "hall_id": 1,
            "hall_name": "Levi",
            "is_active": true
        }
    
    Use Cases:
        - Frontend can call this to verify token is still valid
        - Get user info for displaying in UI (username, role, hall)
        - Check user permissions before showing/hiding UI elements
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role.value,
        hall_id=current_user.hall_id,
        hall_name=current_user.hall.name if current_user.hall else None,
        is_active=current_user.is_active,
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    User logout endpoint.
    
    Note: JWT tokens are stateless, so logout is primarily client-side.
    The client should remove the token from storage (localStorage, etc.).
    
    This endpoint exists for:
    - Completeness of authentication flow
    - Future token blacklisting (if needed)
    - Logging logout events
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        dict: Success message
    
    Example Response:
        {
            "message": "Successfully logged out"
        }
    
    Client-Side Implementation:
        After calling this endpoint, frontend should:
        1. Remove token from localStorage
        2. Redirect to login page
    """
    # JWT is stateless, so we just return success
    # Client should remove token from storage
    # Future: Could implement token blacklist here if needed
    return {"message": "Successfully logged out"}


# ===== Password Recovery Endpoints =====

@router.post("/set-security-question", status_code=status.HTTP_200_OK)
async def set_user_security_question(
    request: SetSecurityQuestionRequest,
    current_user: User = Depends(require_dsa),
    db: Session = Depends(get_db)
):
    """
    Set or update security question for the current user (DSA only).
    
    Only DSA can set security questions. The security answer is hashed
    before storing (like passwords).
    
    Args:
        request: SetSecurityQuestionRequest with question and answer
        current_user: Current authenticated user (must be DSA)
        db: Database session
    
    Returns:
        dict: Success message
    
    Raises:
        HTTPException 400: If question or answer is empty
    """
    set_security_question(
        db=db,
        user_id=current_user.id,
        question=request.question,
        answer=request.answer
    )
    
    return {"message": "Security question set successfully"}


@router.post("/security-question", response_model=SecurityQuestionResponse, status_code=status.HTTP_200_OK)
async def get_user_security_question(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Get security question for a user (public endpoint for forgot password flow).
    
    This endpoint is public (no authentication required) to allow users
    to retrieve their security question when they forget their password.
    
    Args:
        request: ForgotPasswordRequest with username
        db: Database session
    
    Returns:
        SecurityQuestionResponse: Security question if set, None otherwise
    
    Raises:
        HTTPException 404: If user does not exist
    """
    question = get_security_question(db=db, username=request.username)
    
    return SecurityQuestionResponse(
        question=question,
        username=request.username
    )


@router.post("/verify-security-answer", status_code=status.HTTP_200_OK)
async def verify_and_reset_password(
    request: VerifySecurityAnswerRequest,
    db: Session = Depends(get_db)
):
    """
    Verify security answer and reset password (public endpoint).
    
    This endpoint:
    1. Verifies the security answer
    2. If correct, updates the user's password
    3. Returns success message
    
    This endpoint is public (no authentication required) to allow users
    to reset their password when they forget it.
    
    Args:
        request: VerifySecurityAnswerRequest with username, answer, and new_password
        db: Database session
    
    Returns:
        dict: Success message
    
    Raises:
        HTTPException 404: If user does not exist
        HTTPException 400: If security question not set, answer incorrect, or password too short
    """
    reset_password_with_security_question(
        db=db,
        username=request.username,
        answer=request.answer,
        new_password=request.new_password
    )
    
    return {"message": "Password reset successfully. Please login with your new password."}

