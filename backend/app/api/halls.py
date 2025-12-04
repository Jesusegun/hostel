"""
Hall API Endpoints

Provides endpoints for fetching hall information and statistics.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.hall import Hall
from app.models.issue import Issue
from app.api.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/halls", tags=["halls"])


@router.get("/")
def list_halls_with_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all halls with issue statistics.
    
    Returns:
        List of halls with:
        - id, name
        - total_issues
        - pending_issues
        - in_progress_issues
        - done_issues
        - last_issue_created_at
    
    Security:
        - Requires authentication
        - Only admin users can access this endpoint
    """
    # Only admins can see all halls
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin users can view all halls")
    
    # Get all halls
    halls = db.query(Hall).order_by(Hall.name).all()
    
    # Optimize with a single query using subqueries
    from sqlalchemy import case
    
    # Get all issue counts grouped by hall and status in one query
    issue_stats = (
        db.query(
            Issue.hall_id,
            func.count(Issue.id).label("total"),
            func.sum(case((Issue.status == "PENDING", 1), else_=0)).label("pending"),
            func.sum(case((Issue.status == "IN_PROGRESS", 1), else_=0)).label("in_progress"),
            func.sum(case((Issue.status == "DONE", 1), else_=0)).label("done"),
            func.max(Issue.created_at).label("last_created"),
        )
        .group_by(Issue.hall_id)
        .all()
    )
    
    # Create a lookup dict for quick access
    stats_by_hall = {
        stat.hall_id: {
            "total": stat.total or 0,
            "pending": stat.pending or 0,
            "in_progress": stat.in_progress or 0,
            "done": stat.done or 0,
            "last_created": stat.last_created,
        }
        for stat in issue_stats
    }
    
    result = []
    for hall in halls:
        stats = stats_by_hall.get(hall.id, {
            "total": 0,
            "pending": 0,
            "in_progress": 0,
            "done": 0,
            "last_created": None,
        })
        
        result.append(
            {
                "id": hall.id,
                "name": hall.name,
                "total_issues": stats["total"],
                "pending_issues": stats["pending"],
                "in_progress_issues": stats["in_progress"],
                "done_issues": stats["done"],
                "last_issue_created_at": stats["last_created"].isoformat() if stats["last_created"] else None,
            }
        )
    
    return result

