"""
User model for authentication service.

SQLAlchemy model for auth.users table.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    """
    User model for authentication and authorization.
    
    Table: auth.users
    """
    
    __tablename__ = "users"
    __table_args__ = {'schema': 'auth'}
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Unique user identifier"
    )
    
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email address (login username)"
    )
    
    password_hash = Column(
        String(255),
        nullable=False,
        comment="Bcrypt hashed password"
    )
    
    role = Column(
        String(50),
        nullable=False,
        index=True,
        comment="User role: 'employee' or 'manager'"
    )
    
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Account active status"
    )
    
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Account creation timestamp"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Last update timestamp"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
