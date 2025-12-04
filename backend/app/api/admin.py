"""
Admin Management API Routes

Handles admin management endpoints (DSA only):
- User management (create hall admin, reset passwords)
- Hall management (create halls with admin users)
- Category management (CRUD operations)

All endpoints are protected with require_dsa() dependency.
Only the 'dsa' username can access these endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User
from app.dependencies import require_dsa
from app.schemas.admin import (
    CreateHallAdminRequest,
    ResetPasswordResponse,
    UserResponse,
    CreateHallRequest,
    CreateHallResponse,
    HallResponse,
    CreateCategoryRequest,
    UpdateCategoryRequest,
    CategoryResponse,
)
from app.services import admin_service
from app.services.email_service import send_issue_resolved_email
from app.utils.security import create_access_token
from datetime import timedelta

# Create router for admin endpoints
router = APIRouter()


# ===== User Management Endpoints =====

@router.get("/users", response_model=List[UserResponse], status_code=status.HTTP_200_OK)
async def get_all_users(
    current_user: User = Depends(require_dsa),
    db: Session = Depends(get_db)
):
    """
    Get all users in the system.
    
    Returns a list of all users (hall admins and admin users) with their
    associated hall information and basic stats.
    
    Only DSA can access this endpoint.
    
    Returns:
        List[UserResponse]: List of all users
    """
    try:
        users_data = admin_service.get_all_users_with_stats(db)
        # Convert dicts to UserResponse models for proper validation
        users = [UserResponse(**user_dict) for user_dict in users_data]
        return users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users: {str(e)}"
        )


@router.post("/users", response_model=ResetPasswordResponse, status_code=status.HTTP_201_CREATED)
async def create_hall_admin(
    request: CreateHallAdminRequest,
    current_user: User = Depends(require_dsa),
    db: Session = Depends(get_db)
):
    """
    Create a new hall admin user.
    
    Creates a hall admin user for an existing hall. If password is not
    provided, generates a secure random password.
    
    Only DSA can access this endpoint.
    
    Args:
        request: CreateHallAdminRequest with hall_id, username, optional password
    
    Returns:
        ResetPasswordResponse: User information and password in plain text
    
    Raises:
        HTTPException 400: If username already exists or hall not found
    """
    user, password = admin_service.create_hall_admin_user(
        db=db,
        hall_id=request.hall_id,
        username=request.username,
        password=request.password
    )
    
    return ResetPasswordResponse(
        new_password=password,
        user_id=user.id,
        username=user.username
    )


@router.put("/users/{user_id}/password", response_model=ResetPasswordResponse, status_code=status.HTTP_200_OK)
async def reset_user_password(
    user_id: int,
    current_user: User = Depends(require_dsa),
    db: Session = Depends(get_db)
):
    """
    Reset a user's password.
    
    Generates a new secure random password and updates the user's password hash.
    Returns the new password in plain text for display to DSA.
    
    Only DSA can access this endpoint.
    
    Args:
        user_id: ID of the user whose password to reset
    
    Returns:
        ResetPasswordResponse: New password in plain text
    
    Raises:
        HTTPException 404: If user does not exist
    """
    password = admin_service.reset_user_password(db=db, user_id=user_id)
    
    user = db.query(User).filter(User.id == user_id).first()
    
    return ResetPasswordResponse(
        new_password=password,
        user_id=user.id,
        username=user.username
    )


@router.post("/users/{user_id}/unlock", status_code=status.HTTP_200_OK)
async def unlock_user_account(
    user_id: int,
    current_user: User = Depends(require_dsa),
    db: Session = Depends(get_db)
):
    """
    Unlock a user's account.
    
    Clears failed login attempts and lockout time, allowing the user to log in again.
    This is useful when a user has been locked out after 5 failed login attempts.
    
    Only DSA can access this endpoint.
    
    Args:
        user_id: ID of the user to unlock
    
    Returns:
        dict: Success message with user information
    
    Raises:
        HTTPException 404: If user does not exist
    
    Example Response:
        {
            "message": "Account unlocked successfully",
            "user_id": 5,
            "username": "levi"
        }
    """
    user = admin_service.unlock_user(db=db, user_id=user_id)
    
    return {
        "message": "Account unlocked successfully",
        "user_id": user.id,
        "username": user.username
    }


# ===== Hall Management Endpoints =====

@router.get("/halls", response_model=List[HallResponse], status_code=status.HTTP_200_OK)
async def get_all_halls(
    current_user: User = Depends(require_dsa),
    db: Session = Depends(get_db)
):
    """
    Get all halls with issue statistics.
    
    Returns a list of all halls with counts of total, pending, in_progress,
    and done issues for each hall.
    
    Only DSA can access this endpoint.
    
    Returns:
        List[HallResponse]: List of all halls with statistics
    """
    halls = admin_service.get_all_halls_with_stats(db)
    return halls


@router.post("/halls", response_model=CreateHallResponse, status_code=status.HTTP_201_CREATED)
async def create_hall_with_admin(
    request: CreateHallRequest,
    current_user: User = Depends(require_dsa),
    db: Session = Depends(get_db)
):
    """
    Create a new hall and its admin user in a single transaction.
    
    This ensures data integrity - both hall and admin user are created together.
    If password is not provided, generates a secure random password.
    Username is auto-generated from hall_name (lowercase, no spaces) if not provided.
    
    Only DSA can access this endpoint.
    
    Args:
        request: CreateHallRequest with hall_name, optional password and username
    
    Returns:
        CreateHallResponse: Created hall, user, and password in plain text
    
    Raises:
        HTTPException 400: If hall name or username already exists
    """
    hall, user, password = admin_service.create_hall_with_admin(
        db=db,
        hall_name=request.hall_name,
        password=request.password,
        username=request.username  # Optional, auto-generated if not provided
    )
    
    return CreateHallResponse(
        hall={
            "id": hall.id,
            "name": hall.name,
            "created_at": hall.created_at.isoformat() if hall.created_at else None,
        },
        user={
            "id": user.id,
            "username": user.username,
            "role": user.role.value,
            "hall_id": user.hall_id,
        },
        password=password
    )


# ===== Category Management Endpoints =====

@router.get("/categories", response_model=List[CategoryResponse], status_code=status.HTTP_200_OK)
async def get_all_categories(
    current_user: User = Depends(require_dsa),
    db: Session = Depends(get_db)
):
    """
    Get all categories (active and inactive).
    
    Returns a list of all categories with their active status.
    Inactive categories are soft-deleted (preserved for historical data).
    
    Only DSA can access this endpoint.
    
    Returns:
        List[CategoryResponse]: List of all categories
    """
    categories = admin_service.get_all_categories(db)
    return categories


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    request: CreateCategoryRequest,
    current_user: User = Depends(require_dsa),
    db: Session = Depends(get_db)
):
    """
    Create a new issue category.
    
    Only DSA can access this endpoint.
    
    Args:
        request: CreateCategoryRequest with category name
    
    Returns:
        CategoryResponse: Created category information
    
    Raises:
        HTTPException 400: If category name already exists
    """
    category = admin_service.create_category(db=db, name=request.name)
    
    return CategoryResponse(
        id=category.id,
        name=category.name,
        is_active=category.is_active,
        created_at=category.created_at.isoformat() if category.created_at else None,
    )


@router.put("/categories/{category_id}", response_model=CategoryResponse, status_code=status.HTTP_200_OK)
async def update_category(
    category_id: int,
    request: UpdateCategoryRequest,
    current_user: User = Depends(require_dsa),
    db: Session = Depends(get_db)
):
    """
    Update a category's name.
    
    Only DSA can access this endpoint.
    
    Args:
        category_id: ID of the category to update
        request: UpdateCategoryRequest with new category name
    
    Returns:
        CategoryResponse: Updated category information
    
    Raises:
        HTTPException 404: If category does not exist
        HTTPException 400: If new name already exists
    """
    category = admin_service.update_category(
        db=db,
        category_id=category_id,
        name=request.name
    )
    
    return CategoryResponse(
        id=category.id,
        name=category.name,
        is_active=category.is_active,
        created_at=category.created_at.isoformat() if category.created_at else None,
    )


@router.delete("/categories/{category_id}", response_model=CategoryResponse, status_code=status.HTTP_200_OK)
async def delete_category(
    category_id: int,
    current_user: User = Depends(require_dsa),
    db: Session = Depends(get_db)
):
    """
    Soft delete a category by setting is_active to False.
    
    This preserves historical data while hiding the category from
    active use (dropdowns, forms, etc.).
    
    Only DSA can access this endpoint.
    
    Args:
        category_id: ID of the category to soft delete
    
    Returns:
        CategoryResponse: Updated category information (with is_active=False)
    
    Raises:
        HTTPException 404: If category does not exist
    """
    category = admin_service.soft_delete_category(db=db, category_id=category_id)
    
    return CategoryResponse(
        id=category.id,
        name=category.name,
        is_active=category.is_active,
        created_at=category.created_at.isoformat() if category.created_at else None,
    )


@router.post("/categories/{category_id}/activate", response_model=CategoryResponse, status_code=status.HTTP_200_OK)
async def activate_category(
    category_id: int,
    current_user: User = Depends(require_dsa),
    db: Session = Depends(get_db)
):
    """
    Reactivate a previously soft-deleted category.
    
    Sets is_active to True so the category appears in active dropdowns/forms again.
    
    Only DSA can access this endpoint.
    
    Args:
        category_id: ID of the category to reactivate
    
    Returns:
        CategoryResponse: Updated category information (with is_active=True)
    
    Raises:
        HTTPException 404: If category does not exist
    """
    category = admin_service.reactivate_category(db=db, category_id=category_id)
    
    return CategoryResponse(
        id=category.id,
        name=category.name,
        is_active=category.is_active,
        created_at=category.created_at.isoformat() if category.created_at else None,
    )


@router.post("/test-email", status_code=status.HTTP_200_OK)
async def test_email(
    email: str,
    current_user: User = Depends(require_dsa),
):
    """
    Test endpoint to manually trigger an email notification.
    
    This is useful for debugging email delivery issues.
    Only DSA can access this endpoint.
    
    Args:
        email: Email address to send test email to
    
    Returns:
        dict: Status message
    """
    from app.config import settings
    
    # Create a mock issue payload
    test_issue = {
        "id": 999,
        "student_email": email,
        "student_name": "Test User",
        "hall_name": "Test Hall",
        "room_number": "T001",
        "category_name": "Test Category",
        "status": "done",
    }
    
    # Generate a test reopen link
    token = create_access_token(
        {
            "action": "issue_reopen",
            "issue_id": 999,
            "email": email,
        },
        expires_delta=timedelta(hours=72),
    )
    reopen_link = f"{settings.PUBLIC_API_BASE_URL.rstrip('/')}/api/issues/999/reopen?token={token}"
    
    # Send the email (synchronously for testing)
    try:
        send_issue_resolved_email(test_issue, reopen_link)
        return {
            "message": f"Test email sent to {email}",
            "status": "success"
        }
    except Exception as e:
        return {
            "message": f"Failed to send test email: {str(e)}",
            "status": "error"
        }

