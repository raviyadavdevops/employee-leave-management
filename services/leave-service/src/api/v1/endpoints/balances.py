"""Leave balance endpoints."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.services.balance_service import BalanceService
from src.services.allocation_service import AllocationService
from src.schemas.balance import LeaveBalanceResponse
from src.schemas.allocation import AllocateBalancesRequest, AllocationResponse
from shared.common.auth import get_current_user
from shared.common.schemas import UserContext, MessageResponse
from shared.common.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/leave-balances", tags=["Leave Balances"])


@router.get("/me", response_model=List[LeaveBalanceResponse])
async def get_current_employee_balances(
    year: Optional[int] = Query(None, description="Year (default: current year)"),
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's leave balances.
    
    Returns all leave type balances for the specified year.
    """
    service = BalanceService(db)
    return service.get_current_employee_balances(current_user, year)


@router.get("/{employee_id}", response_model=List[LeaveBalanceResponse])
async def get_employee_balances(
    employee_id: UUID,
    year: Optional[int] = Query(None, description="Year (default: current year)"),
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get employee's leave balances.
    
    Authorization:
    - Employees can only view their own balances
    - Managers can view team members' balances
    """
    service = BalanceService(db)
    return service.get_employee_balances(employee_id, current_user, year)


@router.post("/allocate", response_model=AllocationResponse, status_code=status.HTTP_201_CREATED)
async def allocate_employee_balances(
    request: AllocateBalancesRequest,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Allocate leave balances for employee (internal endpoint).
    
    Called by user-service when creating new employees.
    Idempotent: safe to call multiple times for same employee/year.
    """
    service = AllocationService(db)
    return service.allocate_default_balances(request)


@router.get("/{employee_id}/history", response_model=List[dict])
async def get_balance_history(
    employee_id: UUID,
    year: Optional[int] = Query(None, description="Year (default: current year)"),
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get balance transaction history (audit log).
    
    Shows all balance changes: allocations, deductions, refunds, adjustments.
    """
    # Authorization check
    from shared.common.exceptions import ForbiddenException
    if not current_user.is_manager() and employee_id != current_user.user_id:
        raise ForbiddenException(detail="You can only view your own balance history")
    
    # Get balances
    from src.repositories.leave_balance_repository import LeaveBalanceRepository
    from src.repositories.balance_transaction_repository import BalanceTransactionRepository
    from datetime import datetime
    
    if year is None:
        year = datetime.now().year
    
    balance_repo = LeaveBalanceRepository(db)
    transaction_repo = BalanceTransactionRepository(db)
    
    balances = balance_repo.get_employee_balances(employee_id, year)
    
    # Collect all transactions
    all_transactions = []
    for balance in balances:
        transactions = transaction_repo.get_by_balance(balance.id)
        for txn in transactions:
            all_transactions.append({
                "id": str(txn.id),
                "leave_type_id": balance.leave_type_id,
                "transaction_type": txn.transaction_type.value,
                "amount": str(txn.amount),
                "balance_before": str(txn.balance_before),
                "balance_after": str(txn.balance_after),
                "notes": txn.notes,
                "created_at": txn.created_at.isoformat(),
                "created_by": str(txn.created_by) if txn.created_by else None
            })
    
    # Sort by created_at descending
    all_transactions.sort(key=lambda x: x["created_at"], reverse=True)
    
    return all_transactions


@router.get("/{employee_id}/validate", response_model=MessageResponse)
async def validate_balance_consistency(
    employee_id: UUID,
    year: Optional[int] = Query(None, description="Year (default: current year)"),
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate balance consistency (admin/manager only).
    
    Checks: available + provisional + consumed = total_allocated
    """
    from shared.common.exceptions import ForbiddenException
    from datetime import datetime
    
    if not current_user.is_manager():
        raise ForbiddenException(detail="Only managers can validate balances")
    
    if year is None:
        year = datetime.now().year
    
    service = AllocationService(db)
    inconsistencies = service.validate_balance_consistency(employee_id, year)
    
    if inconsistencies:
        return MessageResponse(
            message=f"Found {len(inconsistencies)} balance inconsistencies",
            data={"inconsistencies": inconsistencies}
        )
    
    return MessageResponse(
        message="All balances are consistent",
        data={"year": year}
    )
