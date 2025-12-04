"""
Pydantic Schemas

This package contains Pydantic models for request/response validation and serialization.

Why Pydantic:
- Automatic data validation (type checking, length, format)
- Automatic API documentation (FastAPI uses these for Swagger)
- Type safety (catches errors before they reach database)
- Clear error messages for invalid input
"""

from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    UserResponse,
    TokenData,
)
from app.schemas.issue import (
    IssueResponse,
    IssueListItem,
    IssueListResponse,
    StatusUpdateRequest,
    IssueStatsResponse,
    IssueQueryParams,
)
from app.schemas.dashboard import (
    AdminDashboardResponse,
    KpiMetric,
    CategoryBreakdown,
    HallPerformance,
    TimelinePoint,
)

__all__ = [
    "LoginRequest",
    "LoginResponse",
    "UserResponse",
    "TokenData",
    "IssueResponse",
    "IssueListItem",
    "IssueListResponse",
    "StatusUpdateRequest",
    "IssueStatsResponse",
    "IssueQueryParams",
    "AdminDashboardResponse",
    "KpiMetric",
    "CategoryBreakdown",
    "HallPerformance",
    "TimelinePoint",
]

