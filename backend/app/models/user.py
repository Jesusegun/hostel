"""
User Model

Represents users of the system (hall admins and admin users).

Two types of users:
1. Hall Admins: Manage issues for their specific hall (11 users)
2. Admin Users: Manage all halls and system settings (2 users)

Why this model exists:
- Authentication (login)
- Authorization (who can do what)
- Track who made changes (audit trail)
- Role-based access control

Security Features:
- Account lockout: After 5 failed login attempts, account is locked for 45 minutes
- DSA can manually unlock any user
- Security question recovery also clears the lockout
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
import enum
from app.database import Base


class UserRole(str, enum.Enum):
    """
    User role enumeration
    
    Defines the two types of users in the system.
    Using Enum ensures only valid roles can be assigned.
    """
    HALL_ADMIN = "hall_admin"  # Hall administrator (11 users)
    ADMIN = "admin"            # System administrator (2 users)


class User(Base):
    """
    User Database Model
    
    Represents a user account (hall admin or admin user).
    
    Relationships:
        - One user belongs to one hall (if hall_admin)
        - One user can resolve many issues
        - One user can create many audit logs
    
    Example:
        # Create hall admin
        user = User(
            username="levi",
            password_hash="hashed_password_here",
            role=UserRole.HALL_ADMIN,
            hall_id=1
        )
        
        # Create admin user
        admin = User(
            username="maintenance_officer",
            password_hash="hashed_password_here",
            role=UserRole.ADMIN,
            hall_id=None  # Admin users don't belong to a specific hall
        )
    """
    
    __tablename__ = "users"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Username (unique - for login)
    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Username for login (e.g., 'levi', 'maintenance_officer')"
    )
    
    # Password (hashed with bcrypt - NEVER store plain text passwords!)
    password_hash = Column(
        String(255),
        nullable=False,
        comment="Bcrypt hashed password"
    )
    
    # Security question (optional - only for DSA password recovery)
    security_question = Column(
        String(500),
        nullable=True,
        comment="Security question for password recovery (DSA only)"
    )
    
    # Security answer hash (optional - only for DSA password recovery)
    security_answer_hash = Column(
        String(255),
        nullable=True,
        comment="Hashed security answer (bcrypt, like password_hash)"
    )
    
    # Role (hall_admin or admin)
    role = Column(
        Enum(UserRole),
        nullable=False,
        index=True,
        comment="User role: 'hall_admin' or 'admin'"
    )
    
    # Hall association (only for hall admins, NULL for admin users)
    hall_id = Column(
        Integer,
        ForeignKey("halls.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Hall ID (only for hall_admin role, NULL for admin)"
    )
    
    # Active status (allows disabling accounts without deletion)
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this user account is active"
    )
    
    # Account Lockout Fields (security feature)
    # After 5 failed attempts, account is locked for 45 minutes
    failed_login_attempts = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of consecutive failed login attempts"
    )
    
    locked_until = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Account locked until this time (NULL = not locked)"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="When this user account was created"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="When this user account was last updated"
    )
    
    # Relationships
    # user.hall -> The hall this user manages (None for admin users)
    hall = relationship("Hall", back_populates="users")
    
    # user.resolved_issues -> List of issues this user marked as done
    resolved_issues = relationship("Issue", back_populates="resolved_by_user")
    
    # user.audit_logs -> List of all actions this user performed
    audit_logs = relationship("AuditLog", back_populates="user")
    
    def __repr__(self):
        """String representation (for debugging)"""
        hall_name = self.hall.name if self.hall else "N/A"
        return f"<User(id={self.id}, username='{self.username}', role={self.role.value}, hall='{hall_name}')>"
    
    def to_dict(self, include_sensitive=False):
        """
        Convert to dictionary (for API responses)
        
        Args:
            include_sensitive: Whether to include sensitive data (password_hash)
        
        Returns:
            dict: User data as dictionary
        """
        data = {
            "id": self.id,
            "username": self.username,
            "role": self.role.value,
            "hall_id": self.hall_id,
            "hall_name": self.hall.name if self.hall else None,
            "is_active": self.is_active,
            "has_security_question": bool(self.security_question),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # Only include password_hash if explicitly requested (for internal use)
        if include_sensitive:
            data["password_hash"] = self.password_hash
        
        return data
    
    def is_hall_admin(self):
        """Check if user is a hall admin"""
        return self.role == UserRole.HALL_ADMIN
    
    def is_admin(self):
        """Check if user is an admin"""
        return self.role == UserRole.ADMIN
    
    def can_access_hall(self, hall_id: int) -> bool:
        """
        Check if user can access issues from a specific hall
        
        Args:
            hall_id: The hall ID to check access for
        
        Returns:
            bool: True if user can access this hall's issues
        """
        # Admin users can access all halls
        if self.is_admin():
            return True
        
        # Hall admins can only access their own hall
        return self.hall_id == hall_id
    
    @property
    def is_locked(self) -> bool:
        """
        Check if account is currently locked.
        
        Account is locked if locked_until is set and is in the future.
        If locked_until is in the past, the lockout has expired (auto-unlock after 45 mins).
        
        Returns:
            bool: True if account is currently locked
        """
        if self.locked_until is None:
            return False
        
        # Compare with current UTC time
        # Handle both timezone-aware and timezone-naive datetimes
        now = datetime.now(timezone.utc)
        locked_until = self.locked_until
        
        # If locked_until is timezone-naive, assume it's UTC
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        
        return locked_until > now
    
    @property
    def lockout_remaining_minutes(self) -> int:
        """
        Get the number of minutes remaining until the lockout expires.
        
        Returns:
            int: Minutes remaining (0 if not locked or expired)
        """
        if self.locked_until is None:
            return 0
        
        # Handle both timezone-aware and timezone-naive datetimes
        now = datetime.now(timezone.utc)
        locked_until = self.locked_until
        
        # If locked_until is timezone-naive, assume it's UTC
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        
        if locked_until <= now:
            return 0
        
        remaining = (locked_until - now).total_seconds() / 60
        return max(0, int(remaining))

