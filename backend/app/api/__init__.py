"""
API Routes

This package contains all FastAPI route handlers.

Organized by feature:
- auth.py: Authentication endpoints
- issues.py: Issue management endpoints
- sync.py: Sync endpoints (Google Sheets synchronization)
- dashboard.py: Dashboard/analytics endpoints (to be created)
- admin.py: Admin management endpoints (to be created)
"""

from app.api import auth, dashboard, issues, sync, halls, admin

__all__ = [
    "auth",
    "dashboard",
    "issues",
    "sync",
    "halls",
    "admin",
]

