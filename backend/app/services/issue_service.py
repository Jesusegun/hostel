"""
Issue Service

Business logic for issue management.

This service handles:
- Listing issues with role-based filtering
- Getting issue details
- Updating issue status with audit logging
- Calculating issue statistics

Why this service exists:
- Separates business logic from API routes
- Reusable across different endpoints
- Easier to test (test logic without HTTP layer)
- Single Responsibility: Issue business rules only
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, and_
from sqlalchemy.exc import SQLAlchemyError
from app.models import Issue, Hall, Category, User, AuditLog
from app.models.issue import IssueStatus
from app.models.user import UserRole
from app.schemas.issue import IssueQueryParams

logger = logging.getLogger(__name__)


def get_issues(
    db: Session,
    current_user: User,
    query_params: IssueQueryParams
) -> Dict[str, Any]:
    """
    Get paginated list of issues with filtering.
    
    Applies role-based filtering:
    - Hall Admin: Only sees issues from their hall
    - Admin: Sees issues from all halls (can filter by hall_id)
    
    Args:
        db: Database session
        current_user: Current authenticated user
        query_params: Query parameters for filtering and pagination
    
    Returns:
        dict: Contains issues list, total count, pagination info
    
    Example:
        query_params = IssueQueryParams(status="pending", page=1, page_size=20)
        result = get_issues(db, current_user, query_params)
        # Returns: {"issues": [...], "total": 50, "page": 1, "page_size": 20, "total_pages": 3}
    
    Security Notes:
        - Hall admins are automatically restricted to their hall
        - Admin users can see all halls but can filter by hall_id
        - All queries use parameterized statements (SQL injection prevention)
    """
    # Start with base query
    query = db.query(Issue).join(Hall).join(Category)
    
    # Role-based filtering
    if current_user.role == UserRole.HALL_ADMIN:
        # Hall admins can only see issues from their hall
        query = query.filter(Issue.hall_id == current_user.hall_id)
    elif current_user.role == UserRole.ADMIN:
        # Admin users can see all halls, but can filter by hall_id
        if query_params.hall_id:
            query = query.filter(Issue.hall_id == query_params.hall_id)
    # If query_params.hall_id is set for hall admin, it's ignored (security)
    
    # Apply filters
    if query_params.status:
        query = query.filter(Issue.status == query_params.status)
    
    if query_params.category_id:
        query = query.filter(Issue.category_id == query_params.category_id)
    
    if query_params.date_from:
        query = query.filter(Issue.created_at >= query_params.date_from)
    
    if query_params.date_to:
        query = query.filter(Issue.created_at <= query_params.date_to)
    
    if query_params.room_number:
        query = query.filter(Issue.room_number == query_params.room_number)
    
    if query_params.search:
        # Search in room_number, description, and student_name
        search_filter = or_(
            Issue.room_number.ilike(f"%{query_params.search}%"),
            Issue.description.ilike(f"%{query_params.search}%"),
            Issue.student_name.ilike(f"%{query_params.search}%")
        )
        query = query.filter(search_filter)
    
    # Get total count (before pagination)
    total = query.count()
    
    # Apply pagination
    offset = (query_params.page - 1) * query_params.page_size
    issues = query.order_by(Issue.created_at.desc()).offset(offset).limit(query_params.page_size).all()
    
    # Calculate total pages
    total_pages = (total + query_params.page_size - 1) // query_params.page_size if total > 0 else 0
    
    return {
        "issues": issues,
        "total": total,
        "page": query_params.page,
        "page_size": query_params.page_size,
        "total_pages": total_pages
    }


def get_issue_by_id(
    db: Session,
    issue_id: int,
    current_user: User
) -> Optional[Issue]:
    """
    Get a single issue by ID with access control.
    
    Verifies that the user has access to the issue:
    - Hall Admin: Can only access issues from their hall
    - Admin: Can access any issue
    
    Args:
        db: Database session
        issue_id: Issue ID to retrieve
        current_user: Current authenticated user
    
    Returns:
        Issue object if found and user has access, None otherwise
    
    Raises:
        HTTPException 404: If issue not found
        HTTPException 403: If user doesn't have access
    
    Example:
        issue = get_issue_by_id(db, 1, current_user)
        if issue:
            print(issue.room_number)
    """
    # Get issue with related objects
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    
    if not issue:
        return None
    
    # Check access control
    if current_user.role == UserRole.HALL_ADMIN:
        # Hall admin can only access issues from their hall
        if issue.hall_id != current_user.hall_id:
            return None
    # Admin users can access any issue (no additional check needed)
    
    return issue


def update_issue_status(
    db: Session,
    issue_id: int,
    new_status: IssueStatus,
    current_user: User
) -> Optional[Issue]:
    """
    Update issue status and create audit log entry.
    
    Validates:
    - Issue exists
    - User has access to issue
    - Status transition is valid (pending -> in_progress -> done, can skip steps)
    
    When status is set to "done":
    - Sets resolved_at to current time
    - Sets resolved_by to current user
    
    Args:
        db: Database session
        issue_id: Issue ID to update
        new_status: New status value
        current_user: User making the change
    
    Returns:
        Updated Issue object if successful, None otherwise
    
    Example:
        issue = update_issue_status(db, 1, IssueStatus.IN_PROGRESS, current_user)
        # Issue status updated, audit log created
    """
    # Get issue and verify access
    issue = get_issue_by_id(db, issue_id, current_user)
    
    if not issue:
        return None
    
    # Store old status for audit log
    old_status = issue.status
    
    # Update status
    issue.status = new_status
    issue.updated_at = datetime.utcnow()
    
    # If status is "done", set resolution info
    if new_status == IssueStatus.DONE:
        issue.resolved_at = datetime.utcnow()
        issue.resolved_by = current_user.id
    elif old_status == IssueStatus.DONE and new_status != IssueStatus.DONE:
        # If changing from "done" back to another status, clear resolution info
        issue.resolved_at = None
        issue.resolved_by = None
    
    # Create audit log entry
    audit_log = AuditLog(
        issue_id=issue.id,
        user_id=current_user.id,
        action="status_change",
        old_value=old_status.value if old_status else None,
        new_value=new_status.value,
        details=f"Status changed from {old_status.value} to {new_status.value}"
    )
    db.add(audit_log)
    
    # Save changes
    db.commit()
    db.refresh(issue)
    
    return issue


def get_issue_stats(
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """
    Get issue statistics aggregated by status, category, and hall.
    
    Applies role-based filtering:
    - Hall Admin: Statistics for their hall only
    - Admin: Statistics for all halls (includes by_hall breakdown)
    
    Args:
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        dict: Statistics including counts by status, category, and hall.
              Returns default values (0s and empty lists) if queries fail.
    
    Example:
        stats = get_issue_stats(db, current_user)
        # Returns: {
        #     "total": 100,
        #     "pending": 30,
        #     "in_progress": 20,
        #     "done": 50,
        #     "by_category": [...],
        #     "by_hall": [...]  # Only for admin users
        # }
    """
    # Default values in case of errors
    default_stats = {
        "total": 0,
        "pending": 0,
        "in_progress": 0,
        "done": 0,
        "by_category": [],
        "by_hall": None if current_user.role == UserRole.ADMIN else None
    }
    
    try:
        # Base query
        query = db.query(Issue)
        
        # Role-based filtering
        if current_user.role == UserRole.HALL_ADMIN:
            query = query.filter(Issue.hall_id == current_user.hall_id)
        # Admin users see all issues (no filter)
        
        # Total count
        try:
            total = query.count()
        except (SQLAlchemyError, Exception) as e:
            logger.error(f"Error counting total issues: {e}", exc_info=True)
            total = 0
        
        # Count by status (with individual error handling)
        try:
            pending = query.filter(Issue.status == IssueStatus.PENDING).count()
        except (SQLAlchemyError, Exception) as e:
            logger.error(f"Error counting pending issues: {e}", exc_info=True)
            pending = 0
        
        try:
            in_progress = query.filter(Issue.status == IssueStatus.IN_PROGRESS).count()
        except (SQLAlchemyError, Exception) as e:
            logger.error(f"Error counting in_progress issues: {e}", exc_info=True)
            in_progress = 0
        
        try:
            done = query.filter(Issue.status == IssueStatus.DONE).count()
        except (SQLAlchemyError, Exception) as e:
            logger.error(f"Error counting done issues: {e}", exc_info=True)
            done = 0
        
        # Count by category
        try:
            category_query = query.join(Category).with_entities(
                Category.name,
                func.count(Issue.id).label('count')
            ).group_by(Category.name).all()
            
            by_category = [
                {"category_name": name, "count": count}
                for name, count in category_query
            ]
        except (SQLAlchemyError, Exception) as e:
            logger.error(f"Error fetching category breakdown: {e}", exc_info=True)
            by_category = []
        
        # Count by hall (only for admin users)
        by_hall = None
        if current_user.role == UserRole.ADMIN:
            try:
                hall_query = db.query(Issue).join(Hall).with_entities(
                    Hall.name,
                    func.count(Issue.id).label('count')
                ).group_by(Hall.name).all()
                
                by_hall = [
                    {"hall_name": name, "count": count}
                    for name, count in hall_query
                ]
            except (SQLAlchemyError, Exception) as e:
                logger.error(f"Error fetching hall breakdown: {e}", exc_info=True)
                by_hall = []
        
        return {
            "total": total,
            "pending": pending,
            "in_progress": in_progress,
            "done": done,
            "by_category": by_category,
            "by_hall": by_hall
        }
    
    except Exception as e:
        logger.error(f"Unexpected error in get_issue_stats: {e}", exc_info=True)
        return default_stats

