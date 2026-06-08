"""Allocation service for automatic leave balance allocation."""

from typing import List
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session

from src.repositories.leave_type_repository import LeaveTypeRepository
from src.repositories.leave_balance_repository import LeaveBalanceRepository
from src.repositories.balance_transaction_repository import BalanceTransactionRepository
from src.schemas.allocation import AllocateBalancesRequest, AllocationResponse
from src.models.balance_transaction import TransactionType
from shared.common.logging import get_logger

logger = get_logger(__name__)


class AllocationService:
    """Service for automatic leave balance allocation."""
    
    def __init__(self, db: Session):
        self.db = db
        self.leave_type_repo = LeaveTypeRepository(db)
        self.balance_repo = LeaveBalanceRepository(db)
        self.transaction_repo = BalanceTransactionRepository(db)
    
    def allocate_default_balances(self, request: AllocateBalancesRequest) -> AllocationResponse:
        """
        Allocate default leave balances for new employee.
        
        Steps:
        1. Get all active leave types
        2. Check for existing balances (idempotency)
        3. Create balance records with default allocations
        4. Create transaction audit logs
        """
        employee_id = request.employee_id
        year = request.year if request.year else datetime.now().year
        
        # 1. Get active leave types
        leave_types = self.leave_type_repo.get_all(active_only=True)
        
        if not leave_types:
            logger.warning("No active leave types found")
            return AllocationResponse(
                employee_id=employee_id,
                year=year,
                allocations=[],
                message="No active leave types to allocate"
            )
        
        allocations = []
        
        for leave_type in leave_types:
            # 2. Idempotency check
            existing = self.balance_repo.get_by_employee_and_type(
                employee_id,
                leave_type.id,
                year
            )
            
            if existing:
                logger.info(f"Balance already exists for {employee_id}, {leave_type.name}, {year}")
                continue
            
            # 3. Create balance
            allocation_amount = leave_type.default_allocation
            
            balance = self.balance_repo.create(
                employee_id=employee_id,
                leave_type_id=leave_type.id,
                year=year,
                total_allocated=allocation_amount
            )
            
            # 4. Create transaction log
            self.transaction_repo.create(
                balance_id=balance.id,
                transaction_type=TransactionType.ALLOCATION,
                amount=allocation_amount,
                balance_before=Decimal('0'),
                balance_after=allocation_amount,
                leave_request_id=None,
                notes=f"Initial allocation for {leave_type.display_name}",
                created_by=employee_id
            )
            
            allocations.append({
                "leave_type": leave_type.display_name,
                "amount": str(allocation_amount)
            })
            
            logger.info(f"Allocated {allocation_amount} {leave_type.display_name} to {employee_id}")
        
        return AllocationResponse(
            employee_id=employee_id,
            year=year,
            allocations=allocations,
            message=f"Successfully allocated {len(allocations)} leave types"
        )
    
    def validate_balance_consistency(self, employee_id: UUID, year: int) -> List[dict]:
        """
        Validate balance consistency: available + provisional + consumed = total_allocated.
        
        Returns list of inconsistencies found.
        """
        balances = self.balance_repo.get_employee_balances(employee_id, year)
        inconsistencies = []
        
        for balance in balances:
            total = balance.available + balance.provisional + balance.consumed
            
            if total != balance.total_allocated:
                inconsistencies.append({
                    "balance_id": str(balance.id),
                    "leave_type_id": balance.leave_type_id,
                    "expected": str(balance.total_allocated),
                    "actual": str(total),
                    "difference": str(balance.total_allocated - total)
                })
                
                logger.error(
                    f"Balance inconsistency detected: {balance.id}, "
                    f"expected={balance.total_allocated}, actual={total}"
                )
        
        return inconsistencies
