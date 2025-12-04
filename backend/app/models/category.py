"""
Category Model

Represents issue categories (types of problems).
Examples: Plumbing, Electrical, Carpentry, etc.

Why this model exists:
- Categorize issues for better organization
- Filter issues by category
- Generate reports by category
- Admin can add/edit categories without code changes
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Category(Base):
    """
    Category Database Model
    
    Represents an issue category (type of repair problem).
    
    Relationships:
        - One category has many issues
    
    Example:
        category = Category(name="Plumbing", is_active=True)
        db.add(category)
        db.commit()
    """
    
    __tablename__ = "categories"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Category name (unique - can't have two "Plumbing" categories)
    name = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Category name (e.g., Plumbing, Electrical)"
    )
    
    # Active status (allows soft-deletion - hide instead of delete)
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this category is currently active"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="When this category was created"
    )
    
    # Relationships
    # category.issues -> List of all issues in this category
    issues = relationship("Issue", back_populates="category")
    
    def __repr__(self):
        """String representation (for debugging)"""
        status = "active" if self.is_active else "inactive"
        return f"<Category(id={self.id}, name='{self.name}', status={status})>"
    
    def to_dict(self):
        """
        Convert to dictionary (for API responses)
        
        Returns:
            dict: Category data as dictionary
        """
        return {
            "id": self.id,
            "name": self.name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

