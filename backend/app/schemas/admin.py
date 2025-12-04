"""
Admin Management Schemas

Pydantic models for admin management requests and responses.

These schemas:
- Validate incoming request data (user creation, hall creation, etc.)
- Serialize response data (user lists, hall lists, etc.)
- Provide automatic API documentation
- Ensure type safety throughout the application
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator


# ===== User Management Schemas =====

class CreateHallAdminRequest(BaseModel):
    """
    Request schema for creating a hall admin user.
    
    Fields:
        hall_id: ID of the hall this admin will manage
        username: Username for the hall admin (must be unique)
        password: Optional password (if None, generates random password)
    """
    hall_id: int = Field(..., description="ID of the hall this admin will manage")
    username: str = Field(..., min_length=1, max_length=50, description="Username for the hall admin")
    password: Optional[str] = Field(None, min_length=8, description="Optional password (auto-generated if not provided)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "hall_id": 1,
                "username": "newhall",
                "password": "optional_password"
            }
        }


class ResetPasswordResponse(BaseModel):
    """
    Response schema for password reset.
    
    Contains the new password in plain text (for display to DSA only).
    """
    new_password: str = Field(..., description="New password in plain text (save this, it won't be shown again)")
    user_id: int = Field(..., description="ID of the user whose password was reset")
    username: str = Field(..., description="Username of the user")
    
    class Config:
        json_schema_extra = {
            "example": {
                "new_password": "aB3$kL9mN2pQ",
                "user_id": 5,
                "username": "halladmin"
            }
        }


class UserResponse(BaseModel):
    """
    Response schema for user information.
    
    Used in user list endpoints.
    """
    id: int
    username: str
    role: str
    hall_id: Optional[int] = None
    hall_name: Optional[str] = None
    is_active: bool
    has_security_question: bool
    is_locked: bool = False  # Account lockout status
    lockout_remaining_minutes: int = 0  # Minutes until lockout expires
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True


# ===== Hall Management Schemas =====

class CreateHallRequest(BaseModel):
    """
    Request schema for creating a hall with admin user.
    
    Fields:
        hall_name: Name of the hall to create (must be unique)
        password: Optional password (if None, generates random password)
        username: Optional username (auto-generated from hall_name if not provided)
    
    Username is auto-generated from hall_name (lowercase, no spaces) if not provided.
    """
    hall_name: str = Field(..., min_length=1, max_length=100, description="Name of the hall")
    password: Optional[str] = Field(None, min_length=8, description="Optional password (auto-generated if not provided)")
    username: Optional[str] = Field(None, min_length=1, max_length=50, description="Optional username (auto-generated from hall_name if not provided)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "hall_name": "New Hall",
                "username": "newhall",
                "password": "optional_password",
                "email": "admin@example.com"
            }
        }


class CreateHallResponse(BaseModel):
    """
    Response schema for hall creation.
    
    Contains the created hall, user, and password.
    """
    hall: dict = Field(..., description="Created hall information")
    user: dict = Field(..., description="Created hall admin user information")
    password: str = Field(..., description="Password in plain text (save this, it won't be shown again)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "hall": {"id": 12, "name": "New Hall"},
                "user": {"id": 15, "username": "newhall"},
                "password": "aB3$kL9mN2pQ"
            }
        }


class HallResponse(BaseModel):
    """
    Response schema for hall information with statistics.
    
    Used in hall list endpoints.
    """
    id: int
    name: str
    total: int
    pending: int
    in_progress: int
    done: int
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True


# ===== Category Management Schemas =====

class CreateCategoryRequest(BaseModel):
    """
    Request schema for creating a category.
    
    Fields:
        name: Category name (must be unique)
    """
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "New Category"
            }
        }


class UpdateCategoryRequest(BaseModel):
    """
    Request schema for updating a category name.
    
    Fields:
        name: New category name (must be unique)
    """
    name: str = Field(..., min_length=1, max_length=100, description="New category name")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Category Name"
            }
        }


class CategoryResponse(BaseModel):
    """
    Response schema for category information.
    
    Used in category list endpoints.
    """
    id: int
    name: str
    is_active: bool
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True


# ===== Password Recovery Schemas =====

class SetSecurityQuestionRequest(BaseModel):
    """
    Request schema for setting security question.
    
    Fields:
        question: Security question text
        answer: Security answer (will be hashed before storing)
    """
    question: str = Field(..., min_length=1, max_length=500, description="Security question")
    answer: str = Field(..., min_length=1, description="Security answer")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What city were you born in?",
                "answer": "Lagos"
            }
        }


class ForgotPasswordRequest(BaseModel):
    """
    Request schema for forgot password (step 1: get security question).
    
    Fields:
        username: Username of the user
    """
    username: str = Field(..., min_length=1, max_length=50, description="Username")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "dsa"
            }
        }


class SecurityQuestionResponse(BaseModel):
    """
    Response schema for security question retrieval.
    
    Returns the security question (without the answer).
    """
    question: Optional[str] = Field(None, description="Security question if set, None otherwise")
    username: str = Field(..., description="Username")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What city were you born in?",
                "username": "dsa"
            }
        }


class VerifySecurityAnswerRequest(BaseModel):
    """
    Request schema for verifying security answer and resetting password.
    
    Fields:
        username: Username of the user
        answer: Security answer to verify
        new_password: New password to set
    """
    username: str = Field(..., min_length=1, max_length=50, description="Username")
    answer: str = Field(..., min_length=1, description="Security answer")
    new_password: str = Field(..., min_length=8, description="New password (minimum 8 characters)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "dsa",
                "answer": "Lagos",
                "new_password": "newpassword123"
            }
        }

