"""
Dashboard API Endpoints

Provides analytics data for admin dashboards.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.schemas.dashboard import AdminDashboardResponse
from app.services.dashboard_service import get_admin_dashboard_summary

router = APIRouter()


@router.get(
    "/summary",
    response_model=AdminDashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get admin dashboard analytics",
    description="Returns KPIs, hall/category breakdowns, and timeline data for the admin dashboard.",
)
def get_admin_dashboard_data(
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
    date_from: str | None = Query(
        None,
        description="Start date for filtering (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS). Defaults to 30 days ago.",
    ),
    date_to: str | None = Query(
        None,
        description="End date for filtering (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS). Defaults to now.",
    ),
) -> AdminDashboardResponse:
    """
    Generate analytics required for the admin dashboard.

    Only admin users are allowed to access this endpoint.

    Args:
        current_user: Authenticated admin user (from dependency)
        db: Database session
        date_from: Optional start date for filtering
        date_to: Optional end date for filtering

    Returns:
        AdminDashboardResponse with all analytics data
    """
    # Parse date strings if provided
    parsed_date_from = None
    parsed_date_to = None

    if date_from:
        try:
            # Try parsing with time first, then date only
            try:
                parsed_date_from = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            except ValueError:
                parsed_date_from = datetime.fromisoformat(date_from)
                # If no timezone, assume UTC
                if parsed_date_from.tzinfo is None:
                    from datetime import timezone

                    parsed_date_from = parsed_date_from.replace(tzinfo=timezone.utc)
        except ValueError as e:
            raise ValueError(f"Invalid date_from format: {date_from}. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)") from e

    if date_to:
        try:
            try:
                parsed_date_to = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            except ValueError:
                parsed_date_to = datetime.fromisoformat(date_to)
                # If no timezone, assume UTC
                if parsed_date_to.tzinfo is None:
                    from datetime import timezone

                    parsed_date_to = parsed_date_to.replace(tzinfo=timezone.utc)
        except ValueError as e:
            raise ValueError(f"Invalid date_to format: {date_to}. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)") from e

    # Validate date range
    if parsed_date_from and parsed_date_to and parsed_date_from > parsed_date_to:
        raise ValueError("date_from must be before or equal to date_to")

    return get_admin_dashboard_summary(db, parsed_date_from, parsed_date_to)


