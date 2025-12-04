"""
Hall Model

Represents a hostel/hall in the university.
Examples: Levi, Integrity, Joseph, etc.

Why this model exists:
- Each hall has its own hall admin
- Issues are associated with specific halls
- Allows filtering issues by hall
- Easy to add new halls without code changes
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Hall(Base):
    """
    Hall Database Model
    
    Represents a hostel/hall in the university system.
    
    Relationships:
        - One hall has many users (hall admins)
        - One hall has many issues
    
    Example:
        hall = Hall(name="Levi")
        db.add(hall)
        db.commit()
    """
    
    __tablename__ = "halls"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Hall name (unique - can't have two "Levi" halls)
    name = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Hall name (e.g., Levi, Integrity)"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="When this hall was added to the system"
    )
    
    # Relationships (SQLAlchemy magic - auto-loads related data)
    # These don't create database columns, they create Python properties
    
    # hall.users -> List of all users (hall admins) for this hall
    users = relationship("User", back_populates="hall")
    
    # hall.issues -> List of all issues reported for this hall
    issues = relationship("Issue", back_populates="hall")
    
    def __repr__(self):
        """String representation (for debugging)"""
        return f"<Hall(id={self.id}, name='{self.name}')>"
    
    def to_dict(self):
        """
        Convert to dictionary (for API responses)
        
        Returns:
            dict: Hall data as dictionary
        """
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

