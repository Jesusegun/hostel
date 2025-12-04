"""Issue image retry model definition."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class IssueImageRetry(Base):
    """Tracks pending Cloudinary uploads for issues."""

    __tablename__ = "issue_image_retries"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(
        Integer,
        ForeignKey("issues.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="Issue awaiting Cloudinary upload",
    )
    source_url = Column(
        Text,
        nullable=False,
        comment="Original Google Drive URL captured on the form",
    )
    attempts = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of retry attempts performed so far",
    )
    last_error = Column(
        Text,
        nullable=True,
        comment="Most recent error string if the upload failed",
    )
    last_attempted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of the last retry attempt",
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    issue = relationship("Issue", back_populates="image_retry_entry")

