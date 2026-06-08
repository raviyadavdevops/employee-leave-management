"""Leave balance repository."""

from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.models.leave_balance import LeaveBalance
from shared.common.exceptions import NotFoundException
from shared.common.logging import get_logger

logger = get_logger(__name__)


class LeaveBalanceRepository:
    """Repository for LeaveBalance model with atomic updates."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, balance_id: UUID) -> Optional[LeaveBalance]:
        """Get leave balance by ID."""
        return self.db.query(LeaveBalance).filter(LeaveBalance.id == balance_id).first()
    
    def get_by_employee_and_type(
        self, 
        employee_id: UUID, 
        leave_type_id: int, 
        year: int
    ) -> Optional[LeaveBalance]:
        """Get leave balance for specific employee, type, and year."""
        return self.db.query(LeaveBalance).filter(
            and_(
                LeaveBalance.employee_id == employee_id,
                LeaveBalance.leave_type_id == leave_type_id,
                LeaveBalance.year == year
            )
        ).first()
    
    def get_employee_balances(self, employee_id: UUID, year: int) -> List[LeaveBalance]:
        """Get all leave balances for an employee in a given year."""
        return self.db.query(LeaveBalance).filter(
            and_(
                LeaveBalance.employee_id == employee_id,
                LeaveBalance.year == year
            )
        ).all()
    
    def create(
        self,
        employee_id: UUID,
        leave_type_id: int,
        year: int,
        total_allocated: Decimal
    ) -> LeaveBalance:
        """Create new leave balance."""
        balance = LeaveBalance(
            employee_id=employee_id,
            leave_type_id=leave_type_id,
            year=year,
            total_allocated=total_allocated,
            available=total_allocated,
            provisional=Decimal('0'),
            consumed=Decimal('0')
        )
        self.db.add(balance)
        self.db.commit()
        self.db.refresh(balance)
        logger.info(f"Leave balance created: {balance.id}")
        return balance
    
    def update_atomic(
        self,
        balance_id: UUID,
        available_delta: Decimal = None,
        provisional_delta: Decimal = None,
        consumed_delta: Decimal = None
    ) -> LeaveBalance:
        """
        Atomically update balance fields.
        
        Args:
            balance_id: Balance UUID
            available_delta: Change to available (can be negative)
            provisional_delta: Change to provisional (can be negative)
            consumed_delta: Change to consumed (can be negative)
        """
        balance = self.get_by_id(balance_id)
        if not balance:
            raise NotFoundException(detail=f"Leave balance {balance_id} not found")
        
        if available_delta is not None:
            balance.available += available_delta
        if provisional_delta is not None:
            balance.provisional += provisional_delta
        if consumed_delta is not None:
            balance.consumed += consumed_delta
        
        self.db.commit()
        self.db.refresh(balance)
        logger.info(f"Leave balance updated atomically: {balance.id}")
        return balance
