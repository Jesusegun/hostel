"""
Issue Model

Represents a repair issue/request submitted by a student.

This is the core model of the system - everything revolves around issues.

Why this model exists:
- Store student repair requests
- Track issue status (pending -> in progress -> done)
- Associate issues with halls and categories
- Store image URLs from Cloudinary
- Track who resolved the issue and when
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class IssueStatus(str, enum.Enum):
    """
    Issue status enumeration
    
    Defines the three states an issue can be in.
    Using Enum ensures only valid statuses can be assigned.
    """
    PENDING = "pending"          # Just submitted, not started yet
    IN_PROGRESS = "in_progress"  # Being worked on
    DONE = "done"                # Completed/resolved


class Issue(Base):
    """
    Issue Database Model
    
    Represents a repair issue submitted by a student via Google Form.
    
    Relationships:
        - One issue belongs to one hall
        - One issue belongs to one category
        - One issue is resolved by one user (or none if not resolved yet)
        - One issue has many audit logs
    
    Lifecycle:
        1. Student submits Google Form
        2. System syncs from Google Sheets -> creates Issue (status=pending)
        3. Hall admin marks as "in progress"
        4. Hall admin marks as "done" -> sends email to student
    
    Example:
        issue = Issue(
            student_email="student@example.com",
            student_name="John Doe",
            hall_id=1,
            room_number="A205",
            category_id=1,
            description="Leaking pipe in bathroom",
            image_url="https://res.cloudinary.com/...",
            status=IssueStatus.PENDING
        )
    """
    
    __tablename__ = "issues"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Google Form data
    google_form_timestamp = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Timestamp from Google Form submission"
    )
    
    # Student information
    student_email = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Student's email address (from Google Form)"
    )
    
    student_name = Column(
        String(255),
        nullable=True,
        comment="Student's name (optional field in form)"
    )
    
    # Location information
    hall_id = Column(
        Integer,
        ForeignKey("halls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Which hall this issue is in"
    )
    
    room_number = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Room number (e.g., 'A205', 'B101')"
    )
    
    # Issue details
    category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Category of the issue (Plumbing, Electrical, etc.)"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="Detailed description of the issue"
    )
    
    # Image from Cloudinary
    image_url = Column(
        String(500),
        nullable=True,
        comment="Cloudinary URL of the uploaded image"
    )
    
    # Status tracking
    status = Column(
        Enum(IssueStatus),
        default=IssueStatus.PENDING,
        nullable=False,
        index=True,
        comment="Current status: pending, in_progress, or done"
    )
    
    # Resolution tracking
    resolved_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the issue was marked as done"
    )
    
    resolved_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who marked this issue as done"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="When this issue was created in the system"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="When this issue was last updated"
    )
    
    # Relationships
    # issue.hall -> The hall this issue belongs to
    hall = relationship("Hall", back_populates="issues")
    
    # issue.category -> The category of this issue
    category = relationship("Category", back_populates="issues")
    
    # issue.resolved_by_user -> The user who resolved this issue
    resolved_by_user = relationship("User", back_populates="resolved_issues")
    
    # issue.audit_logs -> List of all changes made to this issue
    audit_logs = relationship("AuditLog", back_populates="issue")

    # Pending image upload entry (if previous upload failed)
    image_retry_entry = relationship(
        "IssueImageRetry",
        back_populates="issue",
        uselist=False
    )
    
    def __repr__(self):
        """String representation (for debugging)"""
        return f"<Issue(id={self.id}, hall='{self.hall.name if self.hall else 'N/A'}', room='{self.room_number}', status={self.status.value})>"
    
    def to_dict(self, include_relations=False):
        """
        Convert to dictionary (for API responses)
        
        Args:
            include_relations: Whether to include related objects (hall, category, user)
        
        Returns:
            dict: Issue data as dictionary
        """
        data = {
            "id": self.id,
            "google_form_timestamp": self.google_form_timestamp.isoformat() if self.google_form_timestamp else None,
            "student_email": self.student_email,
            "student_name": self.student_name,
            "hall_id": self.hall_id,
            "room_number": self.room_number,
            "category_id": self.category_id,
            "description": self.description,
            "image_url": self.image_url,
            "status": self.status.value,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # Include related objects if requested
        if include_relations:
            data["hall_name"] = self.hall.name if self.hall else None
            data["category_name"] = self.category.name if self.category else None
            data["resolved_by_username"] = self.resolved_by_user.username if self.resolved_by_user else None
        
        return data
    
    def is_pending(self):
        """Check if issue is pending"""
        return self.status == IssueStatus.PENDING
    
    def is_in_progress(self):
        """Check if issue is in progress"""
        return self.status == IssueStatus.IN_PROGRESS
    
    def is_done(self):
        """Check if issue is done"""
        return self.status == IssueStatus.DONE
    
    def get_age_in_days(self):
        """
        Calculate how many days since the issue was created
        
        Returns:
            int: Number of days since creation
        """
        from datetime import datetime, timezone
        if self.created_at:
            now = datetime.now(timezone.utc)
            delta = now - self.created_at
            return delta.days
        return 0
    
    def get_resolution_time_in_days(self):
        """
        Calculate how many days it took to resolve the issue
        
        Returns:
            int: Number of days from creation to resolution, or None if not resolved
        """
        if self.resolved_at and self.created_at:
            delta = self.resolved_at - self.created_at
            return delta.days
        return None

