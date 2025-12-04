"""
Sync API Routes

Handles synchronization endpoints:
- POST /api/sync/google-sheets - Manually trigger sync (admin only)
- GET /api/sync/status - Get last sync status and history

Why these endpoints exist:
- Manual sync: Allows admin to trigger sync on-demand (for testing, urgent updates)
- Sync status: Provides visibility into sync health and history
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
from app.database import get_db
from app.models import User, SyncLog, IssueImageRetry
from app.services.sync_service import sync_google_sheets
from app.dependencies import require_admin

logger = logging.getLogger(__name__)

# Create router for sync endpoints
router = APIRouter()


@router.post("/google-sheets", status_code=status.HTTP_200_OK)
async def trigger_sync(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Manually trigger Google Sheets synchronization.
    
    Admin-only endpoint that immediately runs the sync process.
    Useful for:
    - Testing sync functionality
    - Urgent updates (don't wait for scheduled sync)
    - Troubleshooting sync issues
    
    Args:
        current_user: Current authenticated user (must be admin)
        db: Database session
    
    Returns:
        dict: Sync results including:
        - status: "success" or "failed"
        - rows_processed: Number of rows examined
        - rows_created: Number of new issues created
        - rows_skipped: Number of rows skipped (duplicates, errors)
        - errors: List of error messages
    
    Raises:
        HTTPException 403: If user is not admin
    
    Example Request:
        POST /api/sync/google-sheets
        Authorization: Bearer <admin_token>
    
    Example Response:
        {
            "status": "success",
            "rows_processed": 10,
            "rows_created": 5,
            "rows_skipped": 5,
            "errors": [],
            "last_synced_row_index": 10
        }
    """
    logger.info(f"Manual sync triggered by user: {current_user.username}")
    
    try:
        result = sync_google_sheets(db, manual=True)
        
        return {
            "message": "Sync completed",
            "status": result["status"],
            "rows_processed": result["rows_processed"],
            "rows_created": result["rows_created"],
            "rows_skipped": result["rows_skipped"],
            "errors": result.get("errors", []),
            "last_synced_row_index": result.get("last_synced_row_index", 0),
            "retry_summary": result.get("retry_summary")
        }
        
    except Exception as e:
        logger.error(f"Error in manual sync: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.get("/status", status_code=status.HTTP_200_OK)
async def get_sync_status(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = 10
):
    """
    Get sync status and history.
    
    Returns information about the last sync and recent sync history.
    Useful for monitoring sync health and debugging issues.
    
    Args:
        current_user: Current authenticated user (must be admin)
        db: Database session
        limit: Number of recent sync logs to return (default: 10)
    
    Returns:
        dict: Sync status including:
        - last_sync: Last sync information
        - recent_syncs: List of recent sync logs
        - total_syncs: Total number of syncs
    
    Raises:
        HTTPException 403: If user is not admin
    
    Example Request:
        GET /api/sync/status?limit=5
    
    Example Response:
        {
            "last_sync": {
                "id": 10,
                "sync_type": "scheduled",
                "status": "success",
                "started_at": "2025-11-23T10:00:00Z",
                "completed_at": "2025-11-23T10:05:00Z",
                "rows_processed": 10,
                "rows_created": 5,
                "rows_skipped": 5
            },
            "recent_syncs": [...],
            "total_syncs": 100
        }
    """
    last_sync = db.query(SyncLog).order_by(SyncLog.started_at.desc()).first()
    
    recent_syncs = (
        db.query(SyncLog)
        .order_by(SyncLog.started_at.desc())
        .limit(limit)
        .all()
    )
    
    total_syncs = db.query(SyncLog).count()
    
    last_successful = (
        db.query(SyncLog)
        .filter(SyncLog.status == "success")
        .order_by(SyncLog.completed_at.desc())
        .first()
    )
    last_failed = (
        db.query(SyncLog)
        .filter(SyncLog.status == "failed")
        .order_by(SyncLog.completed_at.desc())
        .first()
    )
    
    retry_totals = {
        "entries_checked": sum(sync.retry_entries_checked for sync in recent_syncs),
        "images_uploaded": sum(sync.retry_images_uploaded for sync in recent_syncs),
        "errors": sum(sync.retry_errors for sync in recent_syncs),
    }
    
    pending_image_retries = db.query(IssueImageRetry).count()
    
    return {
        "last_sync": last_sync.to_dict() if last_sync else None,
        "last_successful_sync": last_successful.to_dict() if last_successful else None,
        "last_failed_sync": last_failed.to_dict() if last_failed else None,
        "recent_syncs": [sync.to_dict() for sync in recent_syncs],
        "total_syncs": total_syncs,
        "pending_image_retries": pending_image_retries,
        "recent_retry_totals": retry_totals,
    }

