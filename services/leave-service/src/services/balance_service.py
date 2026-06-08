"""Leave balance service business logic."""

from typing import List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from src.repositories.leave_balance_repository import LeaveBalanceRepository
from src.repositories.leave_type_repository import LeaveTypeRepository
from src.schemas.balance import LeaveBalanceResponse
from shared.common.schemas import UserContext
from shared.common.exceptions import NotFoundException, ForbiddenException
from shared.common.logging import get_logger

logger = get_logger(__name__)


class BalanceService:
    """Service for leave balance management with data scoping."""
    
    def __init__(self, db: Session):
        self.db = db
        self.balance_repo = LeaveBalanceRepository(db)
        self.leave_type_repo = LeaveTypeRepository(db)
    
    def get_employee_balances(
        self,
        employee_id: UUID,
        current_user: UserContext,
        year: int = None
    ) -> List[LeaveBalanceResponse]:
        """
        Get employee leave balances.
        
        Authorization: Employees can only view their own balances.
        """
        # Authorization check
        if not current_user.is_manager() and employee_id != current_user.user_id:
            raise ForbiddenException(detail="You can only view your own leave balances")
        
        # Use current year if not specified
        if year is None:
            year = datetime.now().year
        
        # Get balances
        balances = self.balance_repo.get_employee_balances(employee_id, year)
        
        # Get leave types
        leave_types = {lt.id: lt for lt in self.leave_type_repo.get_all(active_only=True)}
        
        # Build responses
        responses = []
        for balance in balances:
            leave_type = leave_types.get(balance.leave_type_id)
            if not leave_type:
                continue
            
            responses.append(LeaveBalanceResponse(
                id=balance.id,
                employee_id=balance.employee_id,
                leave_type_id=balance.leave_type_id,
                leave_type_name=leave_type.name,
                leave_type_display_name=leave_type.display_name,
                year=balance.year,
                total_allocated=balance.total_allocated,
                available=balance.available,
                provisional=balance.provisional,
                consumed=balance.consumed
            ))
        
        return responses
    
    def get_current_employee_balances(self, current_user: UserContext, year: int = None) -> List[LeaveBalanceResponse]:
        """Get current user's leave balances."""
        return self.get_employee_balances(current_user.user_id, current_user, year)
