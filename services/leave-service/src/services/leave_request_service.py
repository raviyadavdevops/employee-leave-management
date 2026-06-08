"""Leave request service business logic."""

from typing import List, Optional
from uuid import UUID
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session

from src.repositories.leave_request_repository import LeaveRequestRepository
from src.repositories.leave_balance_repository import LeaveBalanceRepository
from src.repositories.leave_type_repository import LeaveTypeRepository
from src.repositories.balance_transaction_repository import BalanceTransactionRepository
from src.schemas.leave_request import CreateLeaveRequestRequest, LeaveRequestResponse, LeaveRequestStatus
from src.models.balance_transaction import TransactionType
from src.services.user_service_client import user_service_client
from src.services.rabbitmq_client import rabbitmq_client
from shared.common.schemas import UserContext
from shared.common.exceptions import NotFoundException, ForbiddenException, BadRequestException, ConflictException
from shared.common.logging import get_logger, get_correlation_id

logger = get_logger(__name__)


class LeaveRequestService:
    """Service for leave request management with business logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.request_repo = LeaveRequestRepository(db)
        self.balance_repo = LeaveBalanceRepository(db)
        self.leave_type_repo = LeaveTypeRepository(db)
        self.transaction_repo = BalanceTransactionRepository(db)
    
    def _calculate_business_days(self, start_date: date, end_date: date) -> Decimal:
        """Calculate business days between start and end dates (inclusive)."""
        # Simple implementation: count all days (in production, exclude weekends/holidays)
        days = (end_date - start_date).days + 1
        return Decimal(str(days))
    
    async def submit_request(
        self,
        request: CreateLeaveRequestRequest,
        current_user: UserContext
    ) -> LeaveRequestResponse:
        """
        Submit leave request with validation and balance updates.
        
        Steps:
        1. Validate leave type exists
        2. Calculate days requested
        3. Check for overlapping requests
        4. Validate sufficient balance
        5. Create leave request
        6. Update balance (available -> provisional)
        7. Create balance transaction
        8. Publish RabbitMQ event
        """
        employee_id = current_user.user_id
        
        # 1. Validate leave type
        leave_type = self.leave_type_repo.get_by_id(request.leave_type_id)
        if not leave_type or not leave_type.is_active:
            raise NotFoundException(detail=f"Leave type {request.leave_type_id} not found or inactive")
        
        # 2. Calculate days
        days_requested = self._calculate_business_days(request.start_date, request.end_date)
        
        # 3. Check for overlaps
        overlaps = self.request_repo.check_overlap(
            employee_id,
            request.start_date,
            request.end_date
        )
        if overlaps:
            overlapping_request = overlaps[0]
            raise ConflictException(
                detail=(
                    "Leave request overlaps with existing request from "
                    f"{overlapping_request.start_date} to {overlapping_request.end_date}"
                )
            )
        
        # 4. Validate sufficient balance
        year = request.start_date.year
        balance = self.balance_repo.get_by_employee_and_type(employee_id, request.leave_type_id, year)
        
        if not balance:
            raise BadRequestException(detail=f"No leave balance found for {leave_type.display_name} in {year}")
        
        if balance.available < days_requested:
            raise BadRequestException(
                detail=f"Insufficient balance. Available: {balance.available}, Requested: {days_requested}"
            )
        
        # 5. Create leave request
        leave_request = self.request_repo.create(
            employee_id=employee_id,
            leave_type_id=request.leave_type_id,
            start_date=request.start_date,
            end_date=request.end_date,
            days_requested=days_requested,
            reason=request.reason,
            status="pending"
        )
        
        # 6. Update balance atomically (available -> provisional)
        balance_before = balance.available
        self.balance_repo.update_atomic(
            balance.id,
            available_delta=-days_requested,
            provisional_delta=days_requested,
            consumed_delta=Decimal('0')
        )
        balance_after = balance_before - days_requested
        
        # 7. Create transaction log
        self.transaction_repo.create(
            balance_id=balance.id,
            transaction_type=TransactionType.DEDUCTION,
            amount=days_requested,
            balance_before=balance_before,
            balance_after=balance_after,
            leave_request_id=leave_request.id,
            notes=f"Provisional deduction for leave request {leave_request.id}",
            created_by=employee_id
        )
        
        # 8. Publish event
        try:
            await rabbitmq_client.publish_event(
                event_type="leave_request_created",
                data={
                    "request_id": str(leave_request.id),
                    "employee_id": str(employee_id),
                    "employee_name": current_user.email,  # In production, fetch full name
                    "leave_type": leave_type.display_name,
                    "start_date": str(request.start_date),
                    "end_date": str(request.end_date),
                    "days_requested": str(days_requested),
                    "manager_id": None  # TODO: Fetch from employee profile
                },
                routing_key="leave_request_created"
            )
            logger.info(f"Published leave_request_created event for {leave_request.id}")
        except Exception as e:
            logger.error(f"Failed to publish event: {str(e)}")
            # Don't fail the request if event publishing fails
        
        return self._build_response(leave_request, leave_type.name)
    
    def get_employee_requests(
        self,
        employee_id: UUID,
        current_user: UserContext,
        status: Optional[str] = None
    ) -> List[LeaveRequestResponse]:
        """
        Get employee's leave requests.
        
        Authorization: Employees can only view their own requests.
        """
        # Authorization
        if not current_user.is_manager() and employee_id != current_user.user_id:
            raise ForbiddenException(detail="You can only view your own leave requests")
        
        requests = self.request_repo.get_employee_requests(employee_id, status)
        
        # Get leave types
        leave_types = {lt.id: lt for lt in self.leave_type_repo.get_all()}
        
        return [self._build_response(req, leave_types.get(req.leave_type_id).name) for req in requests]
    
    def get_request_by_id(
        self,
        request_id: UUID,
        current_user: UserContext
    ) -> LeaveRequestResponse:
        """
        Get leave request by ID.
        
        Authorization: Employees can only view their own requests.
        """
        leave_request = self.request_repo.get_by_id(request_id)
        if not leave_request:
            raise NotFoundException(detail=f"Leave request {request_id} not found")
        
        # Authorization
        if not current_user.is_manager() and leave_request.employee_id != current_user.user_id:
            raise ForbiddenException(detail="You can only view your own leave requests")
        
        leave_type = self.leave_type_repo.get_by_id(leave_request.leave_type_id)
        return self._build_response(leave_request, leave_type.name if leave_type else "Unknown")
    
    async def get_team_requests(
        self,
        current_user: UserContext,
        token: str,
        status: Optional[str] = None
    ) -> List[LeaveRequestResponse]:
        """
        Get leave requests from team members (managers only).
        
        Authorization: Manager role required.
        """
        if not current_user.is_manager():
            raise ForbiddenException(detail="Only managers can view team requests")
        
        # Fetch team member IDs from user service
        try:
            team_member_ids = await user_service_client.get_team_members(
                current_user.user_id,
                token
            )
        except Exception as e:
            logger.error(f"Failed to fetch team members: {str(e)}")
            raise BadRequestException(detail="Failed to fetch team members")
        
        if not team_member_ids:
            return []
        
        # Fetch requests for team members
        requests = self.request_repo.get_team_requests(team_member_ids, status)
        
        # Get leave types
        leave_types = {lt.id: lt for lt in self.leave_type_repo.get_all()}
        
        return [self._build_response(req, leave_types.get(req.leave_type_id).name) for req in requests]
    
    def _build_response(self, leave_request, leave_type_name: str) -> LeaveRequestResponse:
        """Build leave request response."""
        return LeaveRequestResponse(
            id=leave_request.id,
            employee_id=leave_request.employee_id,
            leave_type_id=leave_request.leave_type_id,
            leave_type_name=leave_type_name,
            start_date=leave_request.start_date,
            end_date=leave_request.end_date,
            days_requested=leave_request.days_requested,
            reason=leave_request.reason,
            status=LeaveRequestStatus(leave_request.status),
            reviewed_by=leave_request.reviewed_by,
            reviewed_at=leave_request.reviewed_at.isoformat() if leave_request.reviewed_at else None,
            review_comment=leave_request.review_comment,
            created_at=leave_request.created_at.isoformat(),
            updated_at=leave_request.updated_at.isoformat()
        )
