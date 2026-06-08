"""
Employee model for user service.

SQLAlchemy model for users.employees table with self-referencing manager_id.
"""

import uuid
from datetime import datetime, timezone, date
from sqlalchemy import Column, String, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Employee(Base):
    """
    Employee model for user profiles and reporting hierarchy.
    
    Table: users.employees
    """
    
    __tablename__ = "employees"
    __table_args__ = {'schema': 'users'}
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        comment="References auth.users.id (logical FK)"
    )
    
    first_name = Column(
        String(255),
        nullable=False,
        comment="Employee first name"
    )
    
    last_name = Column(
        String(255),
        nullable=False,
        comment="Employee last name"
    )
    
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Employee email (duplicate from auth for query efficiency)"
    )
    
    department = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Employee department"
    )
    
    manager_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.employees.id'),
        nullable=True,
        index=True,
        comment="Direct manager (self-reference)"
    )
    
    hire_date = Column(
        Date,
        nullable=False,
        comment="Employment start date"
    )
    
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Record creation timestamp"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Last update timestamp"
    )
    
    # Self-referencing relationship for manager
    manager = relationship(
        "Employee",
        remote_side=[id],
        backref="team_members"
    )
    
    def __repr__(self) -> str:
        return f"<Employee(id={self.id}, email={self.email}, name={self.first_name} {self.last_name})>"
    
    @property
    def full_name(self) -> str:
        """Get employee full name."""
        return f"{self.first_name} {self.last_name}"
