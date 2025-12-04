"""
Business Logic Services

This package contains service layer functions that implement business logic.

Why Service Layer:
- Separates business logic from API routes (Separation of Concerns)
- Reusable across different endpoints
- Easier to test (can test logic without HTTP layer)
- Clear responsibility: Services = business rules, Routes = HTTP handling
"""

from app.services.auth_service import (
    authenticate_user,
    get_user_by_username,
)
from app.services.issue_service import (
    get_issues,
    get_issue_by_id,
    update_issue_status,
    get_issue_stats,
)
from app.services.dashboard_service import get_admin_dashboard_summary
from app.services.cloudinary_service import (
    upload_image_from_url,
    upload_image_from_bytes,
)
from app.services.google_sheets_service import (
    fetch_sheet_data,
    parse_form_submission,
    get_image_drive_url,
)
from app.services.sync_service import (
    sync_google_sheets,
    check_duplicate_issue,
    find_or_create_hall,
    find_or_create_category,
)

__all__ = [
    "authenticate_user",
    "get_user_by_username",
    "get_issues",
    "get_issue_by_id",
    "update_issue_status",
    "get_issue_stats",
    "get_admin_dashboard_summary",
    "upload_image_from_url",
    "upload_image_from_bytes",
    "fetch_sheet_data",
    "parse_form_submission",
    "get_image_drive_url",
    "sync_google_sheets",
    "check_duplicate_issue",
    "find_or_create_hall",
    "find_or_create_category",
]

