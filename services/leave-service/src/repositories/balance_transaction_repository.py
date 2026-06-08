"""Balance transaction repository for audit logging."""

from typing import List
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session

from src.models.balance_transaction import BalanceTransaction, TransactionType
from shared.common.logging import get_logger

logger = get_logger(__name__)


class BalanceTransactionRepository:
    """Repository for BalanceTransaction audit log."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_balance(self, balance_id: UUID) -> List[BalanceTransaction]:
        """Get all transactions for a balance."""
        return self.db.query(BalanceTransaction).filter(
            BalanceTransaction.balance_id == balance_id
        ).order_by(BalanceTransaction.created_at.desc()).all()
    
    def get_by_leave_request(self, leave_request_id: UUID) -> List[BalanceTransaction]:
        """Get all transactions for a leave request."""
        return self.db.query(BalanceTransaction).filter(
            BalanceTransaction.leave_request_id == leave_request_id
        ).order_by(BalanceTransaction.created_at.desc()).all()
    
    def create(
        self,
        balance_id: UUID,
        transaction_type: TransactionType,
        amount: Decimal,
        balance_before: Decimal,
        balance_after: Decimal,
        leave_request_id: UUID = None,
        notes: str = None,
        created_by: UUID = None
    ) -> BalanceTransaction:
        """Create audit log transaction."""
        tx_type = transaction_type.value if isinstance(transaction_type, TransactionType) else transaction_type

        transaction = BalanceTransaction(
            balance_id=balance_id,
            transaction_type=tx_type,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            leave_request_id=leave_request_id,
            notes=notes,
            created_by=created_by
        )
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        logger.info(f"Balance transaction created: {transaction.id}")
        return transaction
