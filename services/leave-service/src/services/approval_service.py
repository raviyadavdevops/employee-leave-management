"""Approval service business logic."""

from typing import Optional
from uuid import UUID
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session

from src.repositories.leave_request_repository import LeaveRequestRepository
from src.repositories.leave_balance_repository import LeaveBalanceRepository
from src.repositories.balance_transaction_repository import BalanceTransactionRepository
from src.schemas.approval import ApprovalRequest, RejectionRequest
from src.schemas.leave_request import LeaveRequestResponse
from src.models.balance_transaction import TransactionType
from src.services.user_service_client import user_service_client
from src.services.rabbitmq_client import rabbitmq_client
from shared.common.schemas import UserContext
from shared.common.exceptions import NotFoundException, ForbiddenException, BadRequestException
from shared.common.logging import get_logger

logger = get_logger(__name__)


class ApprovalService:
    """Service for leave request approval and rejection."""
    
    def __init__(self, db: Session):
        self.db = db
        self.request_repo = LeaveRequestRepository(db)
        self.balance_repo = LeaveBalanceRepository(db)
        self.transaction_repo = BalanceTransactionRepository(db)
    
    async def approve_request(
        self,
        request_id: UUID,
        approval: ApprovalRequest,
        current_user: UserContext,
        token: str
    ) -> LeaveRequestResponse:
        """
        Approve leave request with authorization and balance updates.
        
        Steps:
        1. Fetch leave request
        2. Verify manager authorization
        3. Update request status
        4. Update balance (provisional -> consumed)
        5. Create transaction log
        6. Publish RabbitMQ event
        """
        # 1. Fetch request
        leave_request = self.request_repo.get_by_id(request_id)
        if not leave_request:
            raise NotFoundException(detail=f"Leave request {request_id} not found")
        
        if leave_request.status != "pending":
            raise BadRequestException(detail=f"Cannot approve request with status: {leave_request.status}")
        
        # 2. Verify authorization (manager owns this employee)
        try:
            employee_manager_id = await user_service_client.get_employee_manager(
                leave_request.employee_id,
                token
            )
            
            if employee_manager_id != current_user.user_id:
                raise ForbiddenException(
                    detail=f"You can only approve requests from your team members"
                )
        except Exception as e:
            if isinstance(e, (ForbiddenException, BadRequestException)):
                raise
            logger.error(f"Failed to verify manager authorization: {str(e)}")
            raise BadRequestException(detail="Failed to verify manager authorization")
        
        # 3. Update request status
        self.request_repo.update(
            request_id,
            status="approved",
            reviewed_by=current_user.user_id,
            reviewed_at=datetime.now(timezone.utc),
            review_comment=approval.comment
        )
        
        # 4. Update balance (provisional -> consumed)
        year = leave_request.start_date.year
        balance = self.balance_repo.get_by_employee_and_type(
            leave_request.employee_id,
            leave_request.leave_type_id,
            year
        )
        
        if not balance:
            raise BadRequestException(detail="Leave balance not found")
        
        balance_before = balance.consumed
        days = leave_request.days_requested
        
        self.balance_repo.update_atomic(
            balance.id,
            available_delta=Decimal('0'),
            provisional_delta=-days,
            consumed_delta=days
        )
        
        # 5. Create transaction log
        self.transaction_repo.create(
            balance_id=balance.id,
            transaction_type=TransactionType.DEDUCTION,
            amount=days,
            balance_before=balance_before,
            balance_after=balance_before + days,
            leave_request_id=request_id,
            notes=f"Leave approved by manager {current_user.user_id}",
            created_by=current_user.user_id
        )
        
        # 6. Publish event
        try:
            await rabbitmq_client.publish_event(
                event_type="leave_request_approved",
                data={
                    "request_id": str(request_id),
                    "employee_id": str(leave_request.employee_id),
                    "start_date": str(leave_request.start_date),
                    "end_date": str(leave_request.end_date),
                    "approved_by": str(current_user.user_id),
                    "comment": approval.comment
                },
                routing_key="leave_request_approved"
            )
            logger.info(f"Published leave_request_approved event for {request_id}")
        except Exception as e:
            logger.error(f"Failed to publish event: {str(e)}")
        
        # Return updated request
        leave_request = self.request_repo.get_by_id(request_id)
        from src.services.leave_request_service import LeaveRequestService
        service = LeaveRequestService(self.db)
        return service._build_response(leave_request, "Unknown")  # TODO: fetch leave type
    
    async def reject_request(
        self,
        request_id: UUID,
        rejection: RejectionRequest,
        current_user: UserContext,
        token: str
    ) -> LeaveRequestResponse:
        """
        Reject leave request with authorization and balance restoration.
        
        Steps:
        1. Fetch leave request
        2. Verify manager authorization
        3. Update request status
        4. Restore balance (provisional -> available)
        5. Create transaction log
        6. Publish RabbitMQ event
        """
        # 1. Fetch request
        leave_request = self.request_repo.get_by_id(request_id)
        if not leave_request:
            raise NotFoundException(detail=f"Leave request {request_id} not found")
        
        if leave_request.status != "pending":
            raise BadRequestException(detail=f"Cannot reject request with status: {leave_request.status}")
        
        # 2. Verify authorization
        try:
            employee_manager_id = await user_service_client.get_employee_manager(
                leave_request.employee_id,
                token
            )
            
            if employee_manager_id != current_user.user_id:
                raise ForbiddenException(
                    detail="You can only reject requests from your team members"
                )
        except Exception as e:
            if isinstance(e, (ForbiddenException, BadRequestException)):
                raise
            logger.error(f"Failed to verify manager authorization: {str(e)}")
            raise BadRequestException(detail="Failed to verify manager authorization")
        
        # 3. Update request status
        self.request_repo.update(
            request_id,
            status="rejected",
            reviewed_by=current_user.user_id,
            reviewed_at=datetime.now(timezone.utc),
            review_comment=rejection.comment
        )
        
        # 4. Restore balance (provisional -> available)
        year = leave_request.start_date.year
        balance = self.balance_repo.get_by_employee_and_type(
            leave_request.employee_id,
            leave_request.leave_type_id,
            year
        )
        
        if not balance:
            raise BadRequestException(detail="Leave balance not found")
        
        balance_before = balance.available
        days = leave_request.days_requested
        
        self.balance_repo.update_atomic(
            balance.id,
            available_delta=days,
            provisional_delta=-days,
            consumed_delta=Decimal('0')
        )
        
        # 5. Create transaction log
        self.transaction_repo.create(
            balance_id=balance.id,
            transaction_type=TransactionType.REFUND,
            amount=days,
            balance_before=balance_before,
            balance_after=balance_before + days,
            leave_request_id=request_id,
            notes=f"Leave rejected by manager {current_user.user_id}: {rejection.comment}",
            created_by=current_user.user_id
        )
        
        # 6. Publish event
        try:
            await rabbitmq_client.publish_event(
                event_type="leave_request_rejected",
                data={
                    "request_id": str(request_id),
                    "employee_id": str(leave_request.employee_id),
                    "start_date": str(leave_request.start_date),
                    "end_date": str(leave_request.end_date),
                    "rejected_by": str(current_user.user_id),
                    "reason": rejection.comment
                },
                routing_key="leave_request_rejected"
            )
            logger.info(f"Published leave_request_rejected event for {request_id}")
        except Exception as e:
            logger.error(f"Failed to publish event: {str(e)}")
        
        # Return updated request
        leave_request = self.request_repo.get_by_id(request_id)
        from src.services.leave_request_service import LeaveRequestService
        service = LeaveRequestService(self.db)
        return service._build_response(leave_request, "Unknown")
