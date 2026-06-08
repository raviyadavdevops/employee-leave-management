"""Balance transaction model for audit trail."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, Integer, Numeric, ForeignKey, DateTime, Enum as SQLAEnum, Text
from sqlalchemy.dialects.postgresql import UUID

from src.models.base import Base


class TransactionType(str, Enum):
    """Balance transaction type enumeration."""
    ALLOCATION = "allocation"      # Initial allocation
    DEDUCTION = "deduction"        # Leave approved (deduct from available)
    REFUND = "refund"             # Leave cancelled/rejected (add back to available)
    ADJUSTMENT = "adjustment"      # Manual adjustment by admin


class BalanceTransaction(Base):
    """Balance transaction audit log. Table: leaves.balance_transactions"""
    
    __tablename__ = "balance_transactions"
    __table_args__ = {'schema': 'leaves'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    balance_id = Column(UUID(as_uuid=True), ForeignKey('leaves.leave_balances.id'), nullable=False, index=True)
    transaction_type = Column(
        SQLAEnum(
            TransactionType,
            name='transaction_type',
            schema='leaves',
            values_callable=lambda enum_cls: [member.value for member in enum_cls]
        ),
        nullable=False
    )
    amount = Column(Numeric(5, 2), nullable=False, comment="Amount changed (positive or negative)")
    balance_before = Column(Numeric(5, 2), nullable=False, comment="Available balance before transaction")
    balance_after = Column(Numeric(5, 2), nullable=False, comment="Available balance after transaction")
    leave_request_id = Column(UUID(as_uuid=True), nullable=True, comment="Related leave request if applicable")
    notes = Column(Text, nullable=True, comment="Additional notes about the transaction")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True, comment="User who triggered this transaction")
    
    def __repr__(self) -> str:
        return f"<BalanceTransaction(id={self.id}, type={self.transaction_type}, amount={self.amount})>"
