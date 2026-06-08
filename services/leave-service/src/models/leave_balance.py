"""Leave balance model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Numeric, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID

from src.models.base import Base


class LeaveBalance(Base):
    """Leave balance model. Table: leaves.leave_balances"""
    
    __tablename__ = "leave_balances"
    __table_args__ = {'schema': 'leaves'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="References users.employees.id")
    leave_type_id = Column(Integer, ForeignKey('leaves.leave_types.id'), nullable=False)
    year = Column(Integer, nullable=False, comment="Calendar year for this balance")
    total_allocated = Column(Numeric(5, 2), nullable=False, comment="Total days allocated for the year")
    available = Column(Numeric(5, 2), nullable=False, comment="Currently available days")
    provisional = Column(Numeric(5, 2), default=0, nullable=False, comment="Days pending approval (locked)")
    consumed = Column(Numeric(5, 2), default=0, nullable=False, comment="Days used (approved leave)")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self) -> str:
        return f"<LeaveBalance(employee_id={self.employee_id}, leave_type_id={self.leave_type_id}, year={self.year})>"
