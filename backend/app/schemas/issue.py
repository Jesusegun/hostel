"""
Issue Schemas

Pydantic models for issue requests and responses.

These schemas:
- Validate incoming request data (status updates, query parameters)
- Serialize response data (issue details, lists, statistics)
- Provide automatic API documentation
- Ensure type safety throughout the application
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
from app.models.issue import IssueStatus


class IssueResponse(BaseModel):
    """
    Issue Response Schema
    
    Serializes full issue data including related objects.
    Used for single issue responses (GET /api/issues/{id}).
    
    Fields:
        id: Issue ID
        google_form_timestamp: When the form was submitted
        student_email: Student's email address
        student_name: Student's name (optional)
        hall_id: Hall ID
        hall_name: Hall name
        room_number: Room number
        category_id: Category ID
        category_name: Category name
        description: Issue description
        image_url: Cloudinary URL of the image
        status: Current status (pending, in_progress, done)
        resolved_at: When issue was resolved (None if not resolved)
        resolved_by: User ID who resolved the issue
        resolved_by_username: Username who resolved the issue
        created_at: When issue was created
        updated_at: When issue was last updated
        audit_logs: List of audit log entries for this issue
    
    Example:
        {
            "id": 1,
            "student_email": "student@example.com",
            "student_name": "John Doe",
            "hall_id": 1,
            "hall_name": "Levi",
            "room_number": "A205",
            "category_id": 1,
            "category_name": "Plumbing",
            "description": "Leaking pipe",
            "image_url": "https://res.cloudinary.com/...",
            "status": "pending",
            "resolved_at": null,
            "resolved_by": null,
            "resolved_by_username": null,
            "created_at": "2025-11-23T10:00:00Z",
            "updated_at": "2025-11-23T10:00:00Z",
            "audit_logs": []
        }
    """
    id: int
    google_form_timestamp: Optional[datetime] = None
    student_email: str
    student_name: Optional[str] = None
    hall_id: int
    hall_name: Optional[str] = None
    room_number: str
    category_id: int
    category_name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    status: str
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    resolved_by_username: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    audit_logs: Optional[List[dict]] = None
    
    class Config:
        from_attributes = True


class IssueListItem(BaseModel):
    """
    Issue List Item Schema
    
    Simplified issue data for list responses.
    Contains only essential fields for displaying in a list.
    
    Fields:
        id: Issue ID
        student_email: Student's email
        hall_name: Hall name
        room_number: Room number
        category_name: Category name
        status: Current status
        created_at: When issue was created
        image_url: Image URL (for thumbnail)
    
    Example:
        {
            "id": 1,
            "student_email": "student@example.com",
            "hall_name": "Levi",
            "room_number": "A205",
            "category_name": "Plumbing",
            "status": "pending",
            "created_at": "2025-11-23T10:00:00Z",
            "image_url": "https://res.cloudinary.com/..."
        }
    """
    id: int
    student_email: str
    hall_name: Optional[str] = None
    room_number: str
    category_name: Optional[str] = None
    status: str
    created_at: datetime
    image_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class IssueListResponse(BaseModel):
    """
    Issue List Response Schema
    
    Paginated list of issues.
    
    Fields:
        issues: List of issue items
        total: Total number of issues (before pagination)
        page: Current page number
        page_size: Number of items per page
        total_pages: Total number of pages
    
    Example:
        {
            "issues": [...],
            "total": 50,
            "page": 1,
            "page_size": 20,
            "total_pages": 3
        }
    """
    issues: List[IssueListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class StatusUpdateRequest(BaseModel):
    """
    Status Update Request Schema
    
    Validates status update requests.
    
    Fields:
        status: New status (pending, in_progress, or done)
    
    Validation:
        - Must be valid IssueStatus enum value
        - Status transitions are validated in service layer
    
    Example:
        {
            "status": "in_progress"
        }
    """
    status: IssueStatus = Field(..., description="New status for the issue")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "in_progress"
            }
        }


class IssueStatsResponse(BaseModel):
    """
    Issue Statistics Response Schema
    
    Aggregated statistics about issues.
    
    Fields:
        total: Total number of issues
        pending: Number of pending issues
        in_progress: Number of in-progress issues
        done: Number of resolved issues
        by_category: Count of issues by category
        by_hall: Count of issues by hall (only for admin users)
    
    Example:
        {
            "total": 100,
            "pending": 30,
            "in_progress": 20,
            "done": 50,
            "by_category": [
                {"category_name": "Plumbing", "count": 25},
                {"category_name": "Electrical", "count": 15}
            ],
            "by_hall": [
                {"hall_name": "Levi", "count": 10},
                {"hall_name": "Integrity", "count": 8}
            ]
        }
    """
    total: int
    pending: int
    in_progress: int
    done: int
    by_category: List[dict] = Field(default_factory=list)
    by_hall: Optional[List[dict]] = None


class IssueQueryParams(BaseModel):
    """
    Issue Query Parameters Schema
    
    Validates query parameters for GET /api/issues endpoint.
    
    Fields:
        hall_id: Filter by hall (hall admins restricted to their hall)
        status: Filter by status (pending, in_progress, done)
        category_id: Filter by category
        date_from: Filter issues created from this date (ISO format)
        date_to: Filter issues created until this date (ISO format)
        room_number: Filter by room number (exact match)
        search: Search in room_number, description, student_name (partial match)
        page: Page number (default: 1, min: 1)
        page_size: Items per page (default: 20, min: 1, max: 100)
    
    Validation:
        - page: Must be >= 1
        - page_size: Must be between 1 and 100
        - date_from <= date_to (if both provided)
        - status: Must be valid IssueStatus enum
    
    Example Query:
        GET /api/issues?status=pending&page=1&page_size=20&search=A205
    """
    hall_id: Optional[int] = Field(None, description="Filter by hall ID")
    status: Optional[IssueStatus] = Field(None, description="Filter by status")
    category_id: Optional[int] = Field(None, description="Filter by category ID")
    date_from: Optional[datetime] = Field(None, description="Filter issues from this date (ISO format)")
    date_to: Optional[datetime] = Field(None, description="Filter issues until this date (ISO format)")
    room_number: Optional[str] = Field(None, max_length=50, description="Filter by room number (exact match)")
    search: Optional[str] = Field(None, max_length=100, description="Search in room number, description, student name")
    page: int = Field(1, ge=1, description="Page number (starts at 1)")
    page_size: int = Field(20, ge=1, le=100, description="Number of items per page (1-100)")
    
    @validator('date_to')
    def validate_date_range(cls, v, values):
        """Validate that date_to is after date_from"""
        if v and 'date_from' in values and values['date_from']:
            if v < values['date_from']:
                raise ValueError('date_to must be after date_from')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "hall_id": 1,
                "status": "pending",
                "category_id": 1,
                "page": 1,
                "page_size": 20
            }
        }


class IssueReopenRequest(BaseModel):
    """Request body for reopening an issue via token."""

    token: str = Field(..., description="Signed token from the resolution email")
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional note explaining why the issue is still unresolved",
    )


class IssueReopenResult(BaseModel):
    """Response returned when an issue is reopened via token."""

    message: str
    issue_id: int

