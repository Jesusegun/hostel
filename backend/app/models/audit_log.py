"""
Audit Log Model

Tracks all changes made to issues (who did what and when).

Why this model exists:
- Accountability (know who changed what)
- History tracking (see all status changes)
- Debugging (trace back changes)
- Compliance (audit trail for management)

Example use cases:
- "Who marked this issue as done?"
- "When was this issue moved to in progress?"
- "Show me all changes made by user X"
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class AuditLog(Base):
    """
    Audit Log Database Model
    
    Records every change made to an issue.
    
    Relationships:
        - One audit log belongs to one issue
        - One audit log belongs to one user (who made the change)
    
    Example:
        # When hall admin changes status from "pending" to "in_progress"
        log = AuditLog(
            issue_id=123,
            user_id=5,
            action="status_change",
            old_value="pending",
            new_value="in_progress"
        )
    """
    
    __tablename__ = "audit_logs"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Which issue was changed
    issue_id = Column(
        Integer,
        ForeignKey("issues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The issue that was modified"
    )
    
    # Who made the change
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="The user who made this change"
    )
    
    # What action was performed
    action = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Type of action (e.g., 'status_change', 'created', 'updated')"
    )
    
    # What changed
    old_value = Column(
        String(255),
        nullable=True,
        comment="Previous value before the change"
    )
    
    new_value = Column(
        String(255),
        nullable=True,
        comment="New value after the change"
    )
    
    # Additional details (optional)
    details = Column(
        Text,
        nullable=True,
        comment="Additional details about the change"
    )
    
    # When the change happened
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="When this change was made"
    )
    
    # Relationships
    # audit_log.issue -> The issue that was changed
    issue = relationship("Issue", back_populates="audit_logs")
    
    # audit_log.user -> The user who made the change
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        """String representation (for debugging)"""
        user_name = self.user.username if self.user else "System"
        return f"<AuditLog(id={self.id}, issue_id={self.issue_id}, action='{self.action}', user='{user_name}')>"
    
    def to_dict(self, include_relations=False):
        """
        Convert to dictionary (for API responses)
        
        Args:
            include_relations: Whether to include related objects (issue, user)
        
        Returns:
            dict: Audit log data as dictionary
        """
        data = {
            "id": self.id,
            "issue_id": self.issue_id,
            "user_id": self.user_id,
            "action": self.action,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "details": self.details,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
        
        # Include related objects if requested
        if include_relations:
            data["username"] = self.user.username if self.user else "System"
            data["issue_room"] = self.issue.room_number if self.issue else None
        
        return data

