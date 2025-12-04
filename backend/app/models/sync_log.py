"""
Sync Log Model

Tracks Google Sheets synchronization history.

Why this model exists:
- Track when syncs ran (scheduled vs manual)
- Monitor sync success/failure rates
- Debug sync issues (see which rows failed and why)
- Track incremental sync position (last_synced_row_index)
- Provide sync status to admin users
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean
from sqlalchemy.sql import func
from app.database import Base


class SyncLog(Base):
    """
    Sync Log Database Model
    
    Records every Google Sheets synchronization attempt.
    
    Fields:
        id: Primary key
        sync_type: "scheduled" or "manual"
        started_at: When sync started
        completed_at: When sync finished
        status: "success" or "failed"
        rows_processed: Total rows examined
        rows_created: New issues created
        rows_skipped: Rows skipped (duplicates, errors)
        errors: JSON array of error messages
        last_synced_row_index: Last row index processed (for incremental sync)
    
    Example:
        log = SyncLog(
            sync_type="scheduled",
            status="success",
            rows_processed=10,
            rows_created=5,
            rows_skipped=5
        )
    """
    
    __tablename__ = "sync_logs"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Sync type
    sync_type = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Type of sync: 'scheduled' or 'manual'"
    )
    
    # Timestamps
    started_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="When the sync started"
    )
    
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the sync completed"
    )
    
    # Status
    status = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Sync status: 'success' or 'failed'"
    )
    
    # Statistics
    rows_processed = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Total number of rows processed"
    )
    
    rows_created = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of new issues created"
    )
    
    rows_skipped = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of rows skipped (duplicates, errors)"
    )
    
    retry_entries_checked = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of pending image retries examined before this sync"
    )
    
    retry_images_uploaded = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of pending images successfully uploaded during this sync"
    )
    
    retry_errors = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of retry attempts that still failed"
    )
    
    # Error tracking
    errors = Column(
        JSON,
        nullable=True,
        comment="Array of error messages (JSON format)"
    )
    
    # Incremental sync tracking
    last_synced_row_index = Column(
        Integer,
        nullable=True,
        comment="Last row index processed (for incremental sync)"
    )
    
    def __repr__(self):
        """String representation (for debugging)"""
        return f"<SyncLog(id={self.id}, type={self.sync_type}, status={self.status}, created={self.rows_created})>"
    
    def to_dict(self):
        """
        Convert to dictionary (for API responses)
        
        Returns:
            dict: Sync log data as dictionary
        """
        return {
            "id": self.id,
            "sync_type": self.sync_type,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "rows_processed": self.rows_processed,
            "rows_created": self.rows_created,
            "rows_skipped": self.rows_skipped,
            "retry_entries_checked": self.retry_entries_checked,
            "retry_images_uploaded": self.retry_images_uploaded,
            "retry_errors": self.retry_errors,
            "errors": self.errors,
            "last_synced_row_index": self.last_synced_row_index,
        }

