"""Leave request model."""

import uuid
from datetime import datetime, timezone, date
from enum import Enum
from sqlalchemy import Column, String, Integer, Date, Text, ForeignKey, DateTime, Enum as SQLAEnum
from sqlalchemy.dialects.postgresql import UUID

from src.models.base import Base


class LeaveRequestStatus(str, Enum):
    """Leave request status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class LeaveRequest(Base):
    """Leave request model. Table: leaves.leave_requests"""
    
    __tablename__ = "leave_requests"
    __table_args__ = {'schema': 'leaves'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="References users.employees.id")
    leave_type_id = Column(Integer, ForeignKey('leaves.leave_types.id'), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days_requested = Column(Integer, nullable=False, comment="Number of days requested")
    reason = Column(Text, nullable=True, comment="Employee's reason for leave")
    status = Column(
        SQLAEnum(
            LeaveRequestStatus,
            name='leave_request_status',
            schema='leaves',
            values_callable=lambda enum_cls: [member.value for member in enum_cls]
        ),
        default=LeaveRequestStatus.PENDING,
        nullable=False,
        index=True
    )
    reviewed_by = Column(UUID(as_uuid=True), nullable=True, comment="Manager who reviewed the request")
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_comment = Column(Text, nullable=True, comment="Manager's comment on approval/rejection")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self) -> str:
        return f"<LeaveRequest(id={self.id}, employee_id={self.employee_id}, status={self.status})>"
