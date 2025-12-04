"""
Issues API Routes

Handles issue management endpoints:
- GET /api/issues - List issues with filtering and pagination
- GET /api/issues/{id} - Get issue details
- PUT /api/issues/{id}/status - Update issue status
- GET /api/issues/stats - Get issue statistics

Why these endpoints exist:
- List: Display issues in dashboard with filtering
- Detail: Show full issue information
- Status Update: Allow hall admins/admins to update issue status
- Stats: Provide statistics for dashboards
"""

from typing import Optional
from datetime import datetime, timedelta

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    status,
)
from fastapi.responses import HTMLResponse
from jose import JWTError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import AuditLog, Issue, User
from app.models.issue import IssueStatus
from app.schemas.issue import (
    IssueResponse,
    IssueListItem,
    IssueListResponse,
    StatusUpdateRequest,
    IssueStatsResponse,
    IssueQueryParams,
    IssueReopenRequest,
    IssueReopenResult,
)
from app.services.issue_service import (
    get_issues,
    get_issue_by_id,
    update_issue_status,
    get_issue_stats,
)
from app.services.email_service import send_issue_resolved_email
from app.dependencies import require_hall_admin_or_admin
from app.utils.security import create_access_token, decode_access_token

# Create router for issues endpoints
router = APIRouter()


@router.get("", response_model=IssueListResponse, status_code=status.HTTP_200_OK)
async def list_issues(
    hall_id: Optional[int] = Query(None, description="Filter by hall ID"),
    hall: Optional[str] = Query(None, description="Filter by hall name (alternative to hall_id)"),
    status: Optional[IssueStatus] = Query(None, description="Filter by status"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    category: Optional[str] = Query(None, description="Filter by category name (alternative to category_id)"),
    date_from: Optional[datetime] = Query(None, description="Filter issues from this date (ISO format)"),
    date_to: Optional[datetime] = Query(None, description="Filter issues until this date (ISO format)"),
    room_number: Optional[str] = Query(None, max_length=50, description="Filter by room number (exact match)"),
    search: Optional[str] = Query(None, max_length=100, description="Search in room number, description, student name"),
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page (1-100)"),
    current_user: User = Depends(require_hall_admin_or_admin),
    db: Session = Depends(get_db)
):
    """
    List issues with filtering and pagination.
    
    Returns paginated list of issues based on user role:
    - Hall Admin: Only issues from their hall
    - Admin: All issues (can filter by hall_id)
    
    Query Parameters:
        - hall_id: Filter by hall (hall admins restricted to their hall)
        - status: Filter by status (pending, in_progress, done)
        - category_id: Filter by category
        - date_from: Filter issues created from this date
        - date_to: Filter issues created until this date
        - room_number: Filter by room number (exact match)
        - search: Search in room number, description, student name
        - page: Page number (default: 1)
        - page_size: Items per page (default: 20, max: 100)
    
    Returns:
        IssueListResponse: Paginated list of issues
    
    Example Request:
        GET /api/issues?status=pending&page=1&page_size=20
    
    Example Response:
        {
            "issues": [
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
            ],
            "total": 50,
            "page": 1,
            "page_size": 20,
            "total_pages": 3
        }
    """
    # Resolve hall name to hall_id if provided
    resolved_hall_id = hall_id
    if hall and not hall_id:
        from app.models import Hall
        hall_obj = db.query(Hall).filter(Hall.name.ilike(f"%{hall}%")).first()
        if hall_obj:
            resolved_hall_id = hall_obj.id
    
    # Resolve category name to category_id if provided
    resolved_category_id = category_id
    if category and not category_id:
        from app.models import Category
        category_obj = db.query(Category).filter(Category.name.ilike(f"%{category}%")).first()
        if category_obj:
            resolved_category_id = category_obj.id
    
    # Build query params object
    query_params = IssueQueryParams(
        hall_id=resolved_hall_id,
        status=status,
        category_id=resolved_category_id,
        date_from=date_from,
        date_to=date_to,
        room_number=room_number,
        search=search,
        page=page,
        page_size=page_size
    )
    
    # Get issues from service
    result = get_issues(db, current_user, query_params)
    
    # Convert issues to list items
    issue_items = [
        IssueListItem(
            id=issue.id,
            student_email=issue.student_email,
            hall_name=issue.hall.name if issue.hall else None,
            room_number=issue.room_number,
            category_name=issue.category.name if issue.category else None,
            status=issue.status.value,
            created_at=issue.created_at,
            image_url=issue.image_url
        )
        for issue in result["issues"]
    ]
    
    return IssueListResponse(
        issues=issue_items,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"]
    )


@router.get("/stats", response_model=IssueStatsResponse, status_code=status.HTTP_200_OK)
async def get_stats(
    current_user: User = Depends(require_hall_admin_or_admin),
    db: Session = Depends(get_db)
):
    """
    Get issue statistics.
    
    Returns aggregated statistics about issues:
    - Total count
    - Count by status (pending, in_progress, done)
    - Count by category
    - Count by hall (only for admin users)
    
    Statistics are filtered by user role:
    - Hall Admin: Statistics for their hall only
    - Admin: Statistics for all halls
    
    Returns:
        IssueStatsResponse: Aggregated statistics
    
    Example Response (Hall Admin):
        {
            "total": 50,
            "pending": 15,
            "in_progress": 10,
            "done": 25,
            "by_category": [
                {"category_name": "Plumbing", "count": 20},
                {"category_name": "Electrical", "count": 15}
            ],
            "by_hall": null
        }
    
    Example Response (Admin):
        {
            "total": 200,
            "pending": 60,
            "in_progress": 40,
            "done": 100,
            "by_category": [...],
            "by_hall": [
                {"hall_name": "Levi", "count": 20},
                {"hall_name": "Integrity", "count": 18}
            ]
        }
    """
    # Get statistics from service
    stats = get_issue_stats(db, current_user)
    
    return IssueStatsResponse(
        total=stats["total"],
        pending=stats["pending"],
        in_progress=stats["in_progress"],
        done=stats["done"],
        by_category=stats["by_category"],
        by_hall=stats["by_hall"]
    )


@router.get("/{issue_id}", response_model=IssueResponse, status_code=status.HTTP_200_OK)
async def get_issue(
    issue_id: int,
    current_user: User = Depends(require_hall_admin_or_admin),
    db: Session = Depends(get_db)
):
    """
    Get issue details by ID.
    
    Returns full issue information including:
    - All issue fields
    - Related objects (hall, category, resolved_by_user)
    - Audit logs (history of changes)
    
    Args:
        issue_id: Issue ID to retrieve
    
    Returns:
        IssueResponse: Full issue details
    
    Raises:
        HTTPException 404: If issue not found or user doesn't have access
    
    Example Request:
        GET /api/issues/1
    
    Example Response:
        {
            "id": 1,
            "student_email": "student@example.com",
            "hall_name": "Levi",
            "room_number": "A205",
            "category_name": "Plumbing",
            "status": "pending",
            "description": "Leaking pipe in bathroom",
            "image_url": "https://res.cloudinary.com/...",
            "created_at": "2025-11-23T10:00:00Z",
            "audit_logs": [...]
        }
    """
    # Get issue from service (includes access control)
    issue = get_issue_by_id(db, issue_id, current_user)
    
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found or access denied"
        )
    
    # Get audit logs for this issue
    audit_logs = db.query(AuditLog).filter(AuditLog.issue_id == issue_id).order_by(AuditLog.timestamp.desc()).all()
    
    # Convert audit logs to dicts
    audit_logs_data = [
        {
            "id": log.id,
            "user_id": log.user_id,
            "username": log.user.username if log.user else "System",
            "action": log.action,
            "old_value": log.old_value,
            "new_value": log.new_value,
            "details": log.details,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None
        }
        for log in audit_logs
    ]
    
    # Build response
    return IssueResponse(
        id=issue.id,
        google_form_timestamp=issue.google_form_timestamp,
        student_email=issue.student_email,
        student_name=issue.student_name,
        hall_id=issue.hall_id,
        hall_name=issue.hall.name if issue.hall else None,
        room_number=issue.room_number,
        category_id=issue.category_id,
        category_name=issue.category.name if issue.category else None,
        description=issue.description,
        image_url=issue.image_url,
        status=issue.status.value,
        resolved_at=issue.resolved_at,
        resolved_by=issue.resolved_by,
        resolved_by_username=issue.resolved_by_user.username if issue.resolved_by_user else None,
        created_at=issue.created_at,
        updated_at=issue.updated_at,
        audit_logs=audit_logs_data
    )


@router.put("/{issue_id}/status", response_model=IssueResponse, status_code=status.HTTP_200_OK)
async def update_status(
    issue_id: int,
    status_update: StatusUpdateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_hall_admin_or_admin),
    db: Session = Depends(get_db),
):
    """
    Update issue status.
    
    Changes the status of an issue and creates an audit log entry.
    Valid status transitions:
    - pending -> in_progress
    - pending -> done (can skip in_progress)
    - in_progress -> done
    - Any status -> any status (flexible for corrections)
    
    When status is set to "done":
    - Sets resolved_at to current time
    - Sets resolved_by to current user
    
    Args:
        issue_id: Issue ID to update
        status_update: New status value
    
    Returns:
        IssueResponse: Updated issue details
    
    Raises:
        HTTPException 404: If issue not found or user doesn't have access
        HTTPException 400: If status update fails
    
    Example Request:
        PUT /api/issues/1/status
        {
            "status": "in_progress"
        }
    
    Example Response:
        {
            "id": 1,
            "status": "in_progress",
            "updated_at": "2025-11-23T11:00:00Z",
            ...
        }
    """
    previous_issue = get_issue_by_id(db, issue_id, current_user)
    previous_status = previous_issue.status if previous_issue else None
    
    # Update status via service (includes access control and audit logging)
    issue = update_issue_status(db, issue_id, status_update.status, current_user)
    
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found or access denied"
        )
    
    # Get audit logs
    audit_logs = db.query(AuditLog).filter(AuditLog.issue_id == issue_id).order_by(AuditLog.timestamp.desc()).all()
    
    audit_logs_data = [
        {
            "id": log.id,
            "user_id": log.user_id,
            "username": log.user.username if log.user else "System",
            "action": log.action,
            "old_value": log.old_value,
            "new_value": log.new_value,
            "details": log.details,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None
        }
        for log in audit_logs
    ]
    
    # Build response
    response_payload = IssueResponse(
        id=issue.id,
        google_form_timestamp=issue.google_form_timestamp,
        student_email=issue.student_email,
        student_name=issue.student_name,
        hall_id=issue.hall_id,
        hall_name=issue.hall.name if issue.hall else None,
        room_number=issue.room_number,
        category_id=issue.category_id,
        category_name=issue.category.name if issue.category else None,
        description=issue.description,
        image_url=issue.image_url,
        status=issue.status.value,
        resolved_at=issue.resolved_at,
        resolved_by=issue.resolved_by,
        resolved_by_username=issue.resolved_by_user.username if issue.resolved_by_user else None,
        created_at=issue.created_at,
        updated_at=issue.updated_at,
        audit_logs=audit_logs_data
    )

    should_notify = (
        issue.status == IssueStatus.DONE
        and previous_status != IssueStatus.DONE
        and issue.student_email
    )

    if should_notify:
        token = create_access_token(
            {
                "action": "issue_reopen",
                "issue_id": issue.id,
                "email": issue.student_email,
            },
            expires_delta=timedelta(hours=72),
        )
        reopen_link = _build_reopen_link(issue.id, token)
        background_tasks.add_task(
            send_issue_resolved_email,
            response_payload.model_dump(),
            reopen_link,
        )
    
    return response_payload


@router.post(
    "/{issue_id}/reopen",
    response_model=IssueReopenResult,
    status_code=status.HTTP_200_OK,
    summary="Reopen an issue using a token",
)
async def reopen_issue_api(
    issue_id: int,
    payload: IssueReopenRequest,
    db: Session = Depends(get_db),
):
    """
    Reopen an issue using the secure token sent via email.
    """
    issue = _reopen_issue_with_token(db, issue_id, payload.token, payload.reason)
    return IssueReopenResult(
        message="Thanks! We've reopened your ticket and alerted the repair team.",
        issue_id=issue.id,
    )


@router.get(
    "/{issue_id}/reopen",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def reopen_issue_via_link(
    issue_id: int,
    token: str,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Public link used from the resolution email to reopen an issue.
    """
    try:
        issue = _reopen_issue_with_token(db, issue_id, token, reason)
        body = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Issue Reopened - Thank You</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                }}
                .container {{
                    background: white;
                    border-radius: 16px;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                    max-width: 500px;
                    width: 100%;
                    padding: 40px 30px;
                    text-align: center;
                }}
                .success-icon {{
                    width: 80px;
                    height: 80px;
                    background: #10b981;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 24px;
                    animation: scaleIn 0.5s ease-out;
                }}
                .success-icon::after {{
                    content: '✓';
                    color: white;
                    font-size: 48px;
                    font-weight: bold;
                }}
                @keyframes scaleIn {{
                    from {{
                        transform: scale(0);
                        opacity: 0;
                    }}
                    to {{
                        transform: scale(1);
                        opacity: 1;
                    }}
                }}
                h1 {{
                    color: #1f2937;
                    font-size: 28px;
                    font-weight: 700;
                    margin-bottom: 16px;
                }}
                .message {{
                    color: #4b5563;
                    font-size: 16px;
                    line-height: 1.6;
                    margin-bottom: 12px;
                }}
                .issue-id {{
                    color: #6b7280;
                    font-size: 14px;
                    margin-top: 24px;
                }}
                .close-note {{
                    color: #9ca3af;
                    font-size: 14px;
                    margin-top: 32px;
                    padding-top: 24px;
                    border-top: 1px solid #e5e7eb;
                }}
                @media (max-width: 480px) {{
                    .container {{
                        padding: 30px 20px;
                    }}
                    h1 {{
                        font-size: 24px;
                    }}
                    .message {{
                        font-size: 15px;
                    }}
                    .success-icon {{
                        width: 64px;
                        height: 64px;
                    }}
                    .success-icon::after {{
                        font-size: 36px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success-icon"></div>
                <h1>Thank you!</h1>
                <p class="message">Issue #{issue.id} has been re-opened.</p>
                <p class="close-note">You can safely close this tab.</p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(body)
    except HTTPException as exc:
        body = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Unable to Reopen Issue</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                }}
                .container {{
                    background: white;
                    border-radius: 16px;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                    max-width: 500px;
                    width: 100%;
                    padding: 40px 30px;
                    text-align: center;
                }}
                .error-icon {{
                    width: 80px;
                    height: 80px;
                    background: #ef4444;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 24px;
                }}
                .error-icon::after {{
                    content: '✕';
                    color: white;
                    font-size: 48px;
                    font-weight: bold;
                }}
                h1 {{
                    color: #1f2937;
                    font-size: 28px;
                    font-weight: 700;
                    margin-bottom: 16px;
                }}
                .message {{
                    color: #4b5563;
                    font-size: 16px;
                    line-height: 1.6;
                }}
                @media (max-width: 480px) {{
                    .container {{
                        padding: 30px 20px;
                    }}
                    h1 {{
                        font-size: 24px;
                    }}
                    .message {{
                        font-size: 15px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error-icon"></div>
                <h1>Unable to reopen this issue</h1>
                <p class="message">{exc.detail}</p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(body, status_code=exc.status_code)


def _reopen_issue_with_token(
    db: Session,
    issue_id: int,
    token: str,
    reason: Optional[str] = None,
) -> Issue:
    try:
        payload = decode_access_token(token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token.",
        ) from exc
    
    if payload.get("action") != "issue_reopen" or payload.get("issue_id") != issue_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token does not match this issue.",
        )
    
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found.",
        )
    
    token_email = (payload.get("email") or "").lower()
    issue_email = (issue.student_email or "").lower()
    if token_email and token_email != issue_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token email does not match this issue.",
        )
    
    if issue.status != IssueStatus.DONE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Issue is not marked as done.",
        )
    
    issue.status = IssueStatus.PENDING
    issue.resolved_at = None
    issue.resolved_by = None
    
    audit_log = AuditLog(
        issue_id=issue.id,
        user_id=None,
        action="reopened_by_student",
        old_value="done",
        new_value="pending",
        details=reason or "Student reported that the issue is still unresolved.",
    )
    db.add(audit_log)
    db.commit()
    db.refresh(issue)
    return issue


def _build_reopen_link(issue_id: int, token: str) -> str:
    base_url = settings.PUBLIC_API_BASE_URL.rstrip("/")
    return f"{base_url}/api/issues/{issue_id}/reopen?token={token}"

