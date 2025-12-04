"""
Sync Service

Orchestrates Google Sheets synchronization process.

This service coordinates:
- Fetching data from Google Sheets
- Parsing form submissions
- Downloading images from Google Drive
- Uploading images to Cloudinary
- Creating issue records in database
- Tracking sync history

Why this service exists:
- Centralizes sync logic (single responsibility)
- Coordinates multiple services (Google Sheets, Cloudinary, Database)
- Handles error recovery and logging
- Tracks sync progress and history
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging
from app.models import Issue, Hall, Category, AuditLog, SyncLog, IssueImageRetry
from app.models.issue import IssueStatus
from app.services.google_sheets_service import (
    fetch_sheet_data,
    parse_form_submission,
    get_image_drive_url
)
from app.services.cloudinary_service import upload_image_from_url
from app.config import settings

logger = logging.getLogger(__name__)


def check_duplicate_issue(
    db: Session,
    timestamp: Optional[datetime],
    email: str,
    hall_id: Optional[int] = None,
    room_number: Optional[str] = None,
    category_id: Optional[int] = None
) -> bool:
    """
    Check if a duplicate issue already exists.
    
    Duplicate detection prevents processing the same form submission twice.
    Uses multiple strategies:
    1. Exact match: timestamp + email (if timestamp available)
    2. Recent duplicate: email + hall + room + category (within last 24 hours)
    
    Args:
        db: Database session
        timestamp: Google Form submission timestamp (may be None)
        email: Student email address
        hall_id: Hall ID (optional, for enhanced duplicate detection)
        room_number: Room number (optional, for enhanced duplicate detection)
        category_id: Category ID (optional, for enhanced duplicate detection)
    
    Returns:
        True if duplicate found, False otherwise
    
    Example:
        is_duplicate = check_duplicate_issue(
            db, timestamp, "student@example.com", 
            hall_id=1, room_number="A205", category_id=2
        )
        if is_duplicate:
            skip_this_row()
    """
    if not email:
        return False
    
    # Strategy 1: Check exact timestamp + email match (if timestamp available)
    if timestamp:
        existing = db.query(Issue).filter(
            Issue.google_form_timestamp == timestamp,
            Issue.student_email == email
        ).first()
        if existing:
            return True
    
    # Strategy 2: Check for recent duplicate by email + hall + room + category
    # This catches cases where timestamp parsing failed or same issue submitted multiple times
    if hall_id and room_number and category_id:
        from datetime import timedelta
        from app.models.issue import IssueStatus
        
        # Check for pending/in_progress issues with same email, hall, room, category
        # within the last 7 days (to catch duplicates even if timestamps differ)
        recent_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        
        existing = db.query(Issue).filter(
            Issue.student_email == email,
            Issue.hall_id == hall_id,
            Issue.room_number == room_number,
            Issue.category_id == category_id,
            Issue.status.in_([IssueStatus.PENDING, IssueStatus.IN_PROGRESS]),
            Issue.created_at >= recent_cutoff
        ).first()
        
        if existing:
            return True
    
    return False


def find_or_create_hall(
    db: Session,
    hall_name: str
) -> Optional[Hall]:
    """
    Find hall by name (case-insensitive) or return None.
    
    For MVP: Only finds existing halls (doesn't create new ones).
    This ensures data integrity - only admin users can create halls.
    
    Args:
        db: Database session
        hall_name: Hall name to find
    
    Returns:
        Hall object if found, None otherwise
    
    Example:
        hall = find_or_create_hall(db, "Levi")
        if hall:
            print(f"Found hall: {hall.id}")
    """
    # Case-insensitive search
    hall = db.query(Hall).filter(
        func.lower(Hall.name) == hall_name.lower().strip()
    ).first()
    
    return hall


def find_or_create_category(
    db: Session,
    category_name: str
) -> Optional[Category]:
    """
    Find category by name (case-insensitive) or return None.
    
    For MVP: Only finds existing categories (doesn't create new ones).
    This ensures data integrity - only admin users can create categories.
    
    Special handling for "Other" category:
    - When users select "Other" in Google Form, they must type additional text
    - Google Form stores the custom text (e.g., "Whatever", "Something else") as the category
    - We normalize these to "Other" by checking if the category doesn't match any existing category
    - If no match found and it's not a standard category, try matching to "Other"
    
    Args:
        db: Database session
        category_name: Category name to find
    
    Returns:
        Category object if found, None otherwise
    
    Example:
        category = find_or_create_category(db, "Plumbing")
        if category:
            print(f"Found category: {category.id}")
        
        # "Other" with custom text
        category = find_or_create_category(db, "Whatever")  # Will match "Other"
    """
    if not category_name:
        return None
    
    category_name = category_name.strip()
    
    # First, try exact match (case-insensitive)
    category = db.query(Category).filter(
        func.lower(Category.name) == category_name.lower(),
        Category.is_active == True
    ).first()
    
    if category:
        return category
    
    # If no exact match found, check if this might be an "Other" submission
    # Google Form "Other" option requires users to type custom text
    # The category field contains their custom text, not "Other"
    # We need to check if "Other" category exists and use it as fallback
    other_category = db.query(Category).filter(
        func.lower(Category.name) == "other",
        Category.is_active == True
    ).first()
    
    if other_category:
        # This is likely an "Other" submission with custom text
        # Return the "Other" category
        logger.info(f"Category '{category_name}' not found, mapping to 'Other' category")
        return other_category
    
    # No "Other" category exists, return None
    return None


def get_last_synced_row_index(db: Session) -> int:
    """
    Get the last synced row index from the most recent successful sync.
    
    Used for incremental sync - only process rows after this index.
    
    Args:
        db: Database session
    
    Returns:
        Last synced row index (0 if no previous sync)
    """
    last_sync = db.query(SyncLog).filter(
        SyncLog.status == "success"
    ).order_by(SyncLog.completed_at.desc()).first()
    
    if last_sync and last_sync.last_synced_row_index is not None:
        return last_sync.last_synced_row_index
    
    return 0


def enqueue_image_retry(db: Session, issue_id: int, source_url: str, error: str) -> None:
    """
    Store a pending image upload for later retry.
    """
    entry = db.query(IssueImageRetry).filter(IssueImageRetry.issue_id == issue_id).first()
    now = datetime.now(timezone.utc)
    
    if entry:
        entry.source_url = source_url
        entry.last_error = error
        entry.last_attempted_at = now
    else:
        db.add(
            IssueImageRetry(
                issue_id=issue_id,
                source_url=source_url,
                last_error=error,
                last_attempted_at=now
            )
        )


def process_image_retry_queue(db: Session, limit: int = 20) -> Dict[str, Any]:
    """
    Retry pending image uploads (Cloudinary failures) before processing new rows.
    """
    total_pending_before = db.query(IssueImageRetry).count()
    retries = (
        db.query(IssueImageRetry)
        .order_by(IssueImageRetry.created_at)
        .limit(limit)
        .all()
    )
    processed = 0
    uploaded = 0
    failures: List[str] = []
    
    for entry in retries:
        processed += 1
        issue = db.query(Issue).filter(Issue.id == entry.issue_id).first()
        if not issue:
            db.delete(entry)
            db.commit()
            continue
        
        try:
            download_url = get_image_drive_url(entry.source_url)
            cloudinary_url = upload_image_from_url(download_url, issue_id=issue.id)
            if cloudinary_url:
                issue.image_url = cloudinary_url
                db.delete(entry)
                db.commit()
                uploaded += 1
            else:
                entry.attempts += 1
                entry.last_error = "Cloudinary upload returned no URL"
                entry.last_attempted_at = datetime.now(timezone.utc)
                db.commit()
        except Exception as exc:
            entry.attempts += 1
            entry.last_error = str(exc)
            entry.last_attempted_at = datetime.now(timezone.utc)
            db.commit()
            failures.append(str(exc))
    
    pending_after = db.query(IssueImageRetry).count()

    return {
        "entries_checked": processed,
        "images_uploaded": uploaded,
        "errors": failures,
        "errors_count": len(failures),
        "pending_before": total_pending_before,
        "pending_after": pending_after,
    }


def sync_google_sheets(
    db: Session,
    manual: bool = False
) -> Dict[str, Any]:
    """
    Main sync orchestration function.
    
    Fetches new form submissions from Google Sheets, processes them,
    and creates issue records in the database.
    
    Process:
    1. Fetch all rows from Google Sheet
    2. Get last synced row index (for incremental sync)
    3. Process only new rows (after last_synced_row_index)
    4. For each row:
       - Parse form submission
       - Check for duplicates
       - Validate hall and category
       - Download and upload image to Cloudinary
       - Create issue record
       - Create audit log
    5. Track progress and create sync log
    
    Args:
        db: Database session
        manual: True if manually triggered, False if scheduled
    
    Returns:
        Dictionary with sync summary:
        {
            "status": "success" or "failed",
            "rows_processed": int,
            "rows_created": int,
            "rows_skipped": int,
            "errors": List[str],
            "last_synced_row_index": int
        }
    
    Error Handling:
        - Individual row failures don't stop the sync
        - All errors are logged and returned in summary
        - Sync log is created even if sync fails
    """
    sync_log = SyncLog(
        sync_type="manual" if manual else "scheduled",
        status="failed",  # Will update to "success" if completed
        started_at=datetime.now(timezone.utc)
    )
    db.add(sync_log)
    db.commit()
    
    rows_processed = 0
    rows_created = 0
    rows_skipped = 0
    errors = []
    retry_summary = process_image_retry_queue(db)

    logger.info(
        "Image retry queue stats: checked=%s, uploaded=%s, remaining=%s",
        retry_summary.get("entries_checked", 0),
        retry_summary.get("images_uploaded", 0),
        retry_summary.get("pending_after"),
    )

    def _apply_retry_metrics():
        sync_log.retry_entries_checked = retry_summary.get("entries_checked", 0)
        sync_log.retry_images_uploaded = retry_summary.get("images_uploaded", 0)
        sync_log.retry_errors = retry_summary.get("errors_count", 0)
    
    try:
        logger.info(f"Starting Google Sheets sync (manual={manual})")
        
        # Fetch all rows from Google Sheet
        all_rows = fetch_sheet_data(settings.GOOGLE_SHEET_ID)
        
        if not all_rows or len(all_rows) < 2:
            logger.info("No data in Google Sheet (empty or only headers)")
            sync_log.status = "success"
            sync_log.completed_at = datetime.now(timezone.utc)
            sync_log.rows_processed = 0
            sync_log.rows_created = 0
            sync_log.rows_skipped = 0
            sync_log.errors = None
            sync_log.last_synced_row_index = 0
            _apply_retry_metrics()
            db.commit()
            return {
                "status": "success",
                "rows_processed": 0,
                "rows_created": 0,
                "rows_skipped": 0,
                "errors": [],
                "last_synced_row_index": 0,
                "retry_summary": retry_summary,
            }
        
        # First row is headers
        headers = all_rows[0]
        data_rows = all_rows[1:]
        
        # Get last synced row index (for incremental sync)
        start_index = get_last_synced_row_index(db)
        last_synced_row_index = start_index
        logger.info(f"Starting sync from row index: {start_index} (total rows: {len(data_rows)})")
        
        # Process rows starting from last_synced_row_index
        for row_index, row in enumerate(data_rows, start=1):
            # Skip rows we've already processed
            if row_index <= start_index:
                continue
            
            rows_processed += 1
            last_synced_row_index = row_index
            
            try:
                # Parse form submission
                form_data = parse_form_submission(row, headers)
                
                if not form_data:
                    rows_skipped += 1
                    errors.append(f"Row {row_index}: Failed to parse form submission")
                    continue
                
                # Find hall first (needed for duplicate check)
                hall = find_or_create_hall(db, form_data["hall"])
                if not hall:
                    rows_skipped += 1
                    errors.append(f"Row {row_index}: Hall not found: {form_data['hall']}")
                    continue
                
                # Find category first (needed for duplicate check)
                category = find_or_create_category(db, form_data["category"])
                if not category:
                    rows_skipped += 1
                    errors.append(f"Row {row_index}: Category not found: {form_data['category']}")
                    continue
                
                # Check for duplicates (now with hall and category info for better detection)
                if check_duplicate_issue(
                    db, 
                    form_data["timestamp"], 
                    form_data["email"],
                    hall_id=hall.id,
                    room_number=form_data["room_number"],
                    category_id=category.id
                ):
                    rows_skipped += 1
                    logger.info(f"Row {row_index}: Duplicate submission (email={form_data['email']}, hall={form_data['hall']}, room={form_data['room_number']}, category={form_data['category']})")
                    continue
                
                # Create issue record first (without image_url)
                # We need issue.id for Cloudinary folder structure
                issue = Issue(
                    google_form_timestamp=form_data["timestamp"],
                    student_email=form_data["email"],
                    student_name=form_data.get("name"),
                    hall_id=hall.id,
                    room_number=form_data["room_number"],
                    category_id=category.id,
                    description=form_data.get("description"),
                    image_url=None,  # Will be set after upload
                    status=IssueStatus.PENDING
                )
                db.add(issue)
                db.flush()  # Get issue.id without committing
                
                # Process image (download from Drive, upload to Cloudinary)
                cloudinary_url = None
                if form_data.get("image_url"):
                    try:
                        # Convert Google Drive URL to direct download URL
                        download_url = get_image_drive_url(form_data["image_url"])
                        
                        # Upload to Cloudinary with actual issue_id
                        cloudinary_url = upload_image_from_url(download_url, issue_id=issue.id)
                        
                        if cloudinary_url:
                            issue.image_url = cloudinary_url
                        else:
                            message = "Cloudinary upload returned no URL, queued for retry"
                            enqueue_image_retry(db, issue.id, form_data["image_url"], message)
                            errors.append(f"Row {row_index}: {message}")
                            logger.warning(f"Row {row_index}: {message}")
                    except Exception as e:
                        logger.error(f"Row {row_index}: Error processing image: {e}")
                        enqueue_image_retry(db, issue.id, form_data["image_url"], str(e))
                        errors.append(f"Row {row_index}: Image processing error queued for retry")
                
                # Create audit log entry
                audit_log = AuditLog(
                    issue_id=issue.id,
                    user_id=None,  # System action
                    action="created",
                    old_value=None,
                    new_value="pending",
                    details="Issue created from Google Form submission"
                )
                db.add(audit_log)
                
                db.commit()
                rows_created += 1
                last_synced_row_index = row_index
                
                logger.info(f"Row {row_index}: Created issue {issue.id} for {form_data['email']}")
                
            except Exception as e:
                db.rollback()
                rows_skipped += 1
                error_msg = f"Row {row_index}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
                continue
        
        # Update sync log
        sync_log.status = "success"
        sync_log.completed_at = datetime.now(timezone.utc)
        sync_log.rows_processed = rows_processed
        sync_log.rows_created = rows_created
        sync_log.rows_skipped = rows_skipped
        sync_log.errors = errors if errors else None
        sync_log.last_synced_row_index = last_synced_row_index
        _apply_retry_metrics()
        db.commit()
        
        logger.info(f"Sync completed: {rows_created} created, {rows_skipped} skipped, {len(errors)} errors")
        
        return {
            "status": "success",
            "rows_processed": rows_processed,
            "rows_created": rows_created,
            "rows_skipped": rows_skipped,
            "errors": errors,
            "last_synced_row_index": last_synced_row_index,
            "retry_summary": retry_summary
        }
        
    except Exception as e:
        db.rollback()
        error_msg = f"Sync failed: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
        
        # Update sync log with failure
        sync_log.status = "failed"
        sync_log.completed_at = datetime.now(timezone.utc)
        sync_log.rows_processed = rows_processed
        sync_log.rows_created = rows_created
        sync_log.rows_skipped = rows_skipped
        sync_log.errors = errors
        sync_log.last_synced_row_index = last_synced_row_index
        _apply_retry_metrics()
        db.commit()
        
        return {
            "status": "failed",
            "rows_processed": rows_processed,
            "rows_created": rows_created,
            "rows_skipped": rows_skipped,
            "errors": errors,
            "last_synced_row_index": last_synced_row_index,
            "retry_summary": retry_summary
        }

