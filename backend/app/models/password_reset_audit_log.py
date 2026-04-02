"""
Password Reset Audit Log Model

Tracks password reset request and completion events for security auditing.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class PasswordResetAuditLog(Base):
    """Audit entries for forgot-password and token-reset events."""

    __tablename__ = "password_reset_audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Resolved user ID when known"
    )

    action = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Event type: request, request_blocked, reset_success, reset_failure"
    )

    success = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether the event completed successfully"
    )

    identifier_input = Column(
        String(255),
        nullable=True,
        comment="Username/email identifier submitted by client"
    )

    request_ip = Column(
        String(64),
        nullable=True,
        index=True,
        comment="Client IP address for abuse monitoring"
    )

    user_agent = Column(
        String(255),
        nullable=True,
        comment="User-Agent header (truncated)"
    )

    reason = Column(
        String(255),
        nullable=True,
        comment="Failure/block reason when relevant"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="Event creation time"
    )

    user = relationship("User")
