"""Leave request endpoints."""

from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, Query, status, Header
from sqlalchemy.orm import Session

from src.database import get_db
from src.services.leave_request_service import LeaveRequestService
from src.services.approval_service import ApprovalService
from src.services.calendar_service import CalendarService
from src.schemas.leave_request import CreateLeaveRequestRequest, LeaveRequestResponse
from src.schemas.approval import ApprovalRequest, RejectionRequest
from src.schemas.calendar import TeamCalendarResponse
from shared.common.auth import get_current_user, get_current_manager
from shared.common.schemas import UserContext
from shared.common.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/leave-requests", tags=["Leave Requests"])


@router.post("/", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED)
async def submit_leave_request(
    request: CreateLeaveRequestRequest,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit a leave request.
    
    Validates:
    - Sufficient leave balance
    - No overlapping requests
    - Valid leave type
    
    Automatically updates balance (available -> provisional).
    Publishes event to RabbitMQ for notifications.
    """
    service = LeaveRequestService(db)
    return await service.submit_request(request, current_user)


@router.get("/", response_model=List[LeaveRequestResponse])
async def get_current_employee_requests(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's leave requests.
    
    Optionally filter by status: pending, approved, rejected, cancelled.
    """
    service = LeaveRequestService(db)
    return service.get_employee_requests(current_user.user_id, current_user, status_filter)


@router.get("/{request_id}", response_model=LeaveRequestResponse)
async def get_leave_request(
    request_id: UUID,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get leave request by ID.
    
    Authorization: Employees can only view their own requests.
    """
    service = LeaveRequestService(db)
    return service.get_request_by_id(request_id, current_user)


@router.get("/team/requests", response_model=List[LeaveRequestResponse])
async def get_team_leave_requests(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    current_user: UserContext = Depends(get_current_manager),
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Get team members' leave requests (managers only).
    
    Returns pending/approved/rejected requests from all team members.
    """
    # Extract token from Authorization header
    token = authorization.replace("Bearer ", "")
    
    service = LeaveRequestService(db)
    return await service.get_team_requests(current_user, token, status_filter)


@router.post("/{request_id}/approve", response_model=LeaveRequestResponse)
async def approve_leave_request(
    request_id: UUID,
    approval: ApprovalRequest,
    current_user: UserContext = Depends(get_current_manager),
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Approve leave request (managers only).
    
    Authorization: Manager must be the employee's direct manager.
    
    Actions:
    - Updates request status to 'approved'
    - Moves balance from provisional to consumed
    - Creates transaction log
    - Publishes approval event to RabbitMQ
    """
    token = authorization.replace("Bearer ", "")
    
    service = ApprovalService(db)
    return await service.approve_request(request_id, approval, current_user, token)


@router.post("/{request_id}/reject", response_model=LeaveRequestResponse)
async def reject_leave_request(
    request_id: UUID,
    rejection: RejectionRequest,
    current_user: UserContext = Depends(get_current_manager),
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Reject leave request (managers only).
    
    Authorization: Manager must be the employee's direct manager.
    Rejection comment is mandatory.
    
    Actions:
    - Updates request status to 'rejected'
    - Restores balance from provisional to available
    - Creates transaction log
    - Publishes rejection event to RabbitMQ
    """
    token = authorization.replace("Bearer ", "")
    
    service = ApprovalService(db)
    return await service.reject_request(request_id, rejection, current_user, token)


@router.get("/team/calendar", response_model=TeamCalendarResponse)
async def get_team_calendar(
    start_date: Optional[date] = Query(None, description="Start date for calendar"),
    end_date: Optional[date] = Query(None, description="End date for calendar"),
    current_user: UserContext = Depends(get_current_manager),
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Get team calendar with coverage warnings (managers only).
    
    Shows approved leave and highlights coverage gaps:
    - Warning: >30% of team on leave
    - Critical: >50% of team on leave
    """
    token = authorization.replace("Bearer ", "")
    
    service = CalendarService(db)
    return await service.get_team_calendar(current_user, token, start_date, end_date)
