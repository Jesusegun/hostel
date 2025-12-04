"""
Authentication Schemas

Pydantic models for authentication requests and responses.

These schemas:
- Validate incoming request data (username, password format)
- Serialize response data (user info, tokens)
- Provide automatic API documentation
- Ensure type safety throughout the application
"""

from typing import Optional
from pydantic import BaseModel, Field, validator


class LoginRequest(BaseModel):
    """
    Login Request Schema
    
    Validates login form data from frontend.
    
    Fields:
        username: User's username (hall name for hall admins, or admin username)
        password: User's password (plain text, will be hashed/verified)
    
    Validation:
        - Username: Non-empty string, max 50 characters (matches User model)
        - Password: Non-empty string, minimum 8 characters (security requirement)
    
    Example:
        {
            "username": "levi",
            "password": "changeme123"
        }
    """
    username: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Username for login (e.g., 'levi', 'maintenance_officer')"
    )
    password: str = Field(
        ...,
        min_length=8,
        description="User's password (minimum 8 characters)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "levi",
                "password": "changeme123"
            }
        }


class UserResponse(BaseModel):
    """
    User Response Schema
    
    Serializes user data for API responses.
    Excludes sensitive information (password_hash).
    
    Fields:
        id: User's database ID
        username: User's login username
        role: User's role (hall_admin or admin)
        hall_id: Associated hall ID (None for admin users)
        hall_name: Hall name (None for admin users)
        is_active: Whether account is active
    
    Example:
        {
            "id": 1,
            "username": "levi",
            "role": "hall_admin",
            "hall_id": 1,
            "hall_name": "Levi",
            "is_active": true
        }
    """
    id: int
    username: str
    role: str
    hall_id: Optional[int] = None
    hall_name: Optional[str] = None
    is_active: bool
    
    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy models


class LoginResponse(BaseModel):
    """
    Login Response Schema
    
    Returned after successful login.
    Contains JWT token and user information.
    
    Fields:
        access_token: JWT token for authentication
        token_type: Token type (always "bearer" for JWT)
        user: User information (UserResponse)
    
    Example:
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
    """
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="Authenticated user information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJsZXZpIiwicm9sZSI6ImhhbGxfYWRtaW4iLCJoYWxsX2lkIjoxLCJleHAiOjE2MDAwMDAwMDB9.signature",
                "token_type": "bearer",
                "user": {
                    "id": 1,
                    "username": "levi",
                    "role": "hall_admin",
                    "hall_id": 1,
                    "hall_name": "Levi",
                    "is_active": True
                }
            }
        }


class TokenData(BaseModel):
    """
    Token Data Schema
    
    Represents data extracted from JWT token payload.
    Used internally for token validation.
    
    Fields:
        username: Username from token (sub claim)
        role: User role from token
        hall_id: Hall ID from token (optional, None for admin users)
    
    Note:
        This is not used in API responses, only for internal token processing.
    """
    username: Optional[str] = None
    role: Optional[str] = None
    hall_id: Optional[int] = None

