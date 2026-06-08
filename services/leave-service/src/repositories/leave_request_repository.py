"""Leave request repository."""

from typing import List, Optional
from uuid import UUID
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.models.leave_request import LeaveRequest, LeaveRequestStatus
from shared.common.exceptions import NotFoundException
from shared.common.logging import get_logger

logger = get_logger(__name__)


class LeaveRequestRepository:
    """Repository for LeaveRequest model with overlap checks."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, request_id: UUID) -> Optional[LeaveRequest]:
        """Get leave request by ID."""
        return self.db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
    
    def get_employee_requests(
        self, 
        employee_id: UUID, 
        status: Optional[LeaveRequestStatus] = None
    ) -> List[LeaveRequest]:
        """Get leave requests for an employee, optionally filtered by status."""
        query = self.db.query(LeaveRequest).filter(LeaveRequest.employee_id == employee_id)
        if status:
            query = query.filter(LeaveRequest.status == status)
        return query.order_by(LeaveRequest.created_at.desc()).all()
    
    def get_team_requests(
        self,
        employee_ids: List[UUID],
        status: Optional[LeaveRequestStatus] = None
    ) -> List[LeaveRequest]:
        """Get leave requests for a team of employees."""
        query = self.db.query(LeaveRequest).filter(LeaveRequest.employee_id.in_(employee_ids))
        if status:
            query = query.filter(LeaveRequest.status == status)
        return query.order_by(LeaveRequest.created_at.desc()).all()
    
    def check_overlap(
        self,
        employee_id: UUID,
        start_date: date,
        end_date: date,
        exclude_request_id: Optional[UUID] = None
    ) -> List[LeaveRequest]:
        """
        Check for overlapping leave requests.
        
        Returns approved or pending requests that overlap with the given date range.
        """
        query = self.db.query(LeaveRequest).filter(
            and_(
                LeaveRequest.employee_id == employee_id,
                LeaveRequest.status.in_([LeaveRequestStatus.APPROVED, LeaveRequestStatus.PENDING]),
                or_(
                    # Case 1: Existing request starts within new request
                    and_(
                        LeaveRequest.start_date >= start_date,
                        LeaveRequest.start_date <= end_date
                    ),
                    # Case 2: Existing request ends within new request
                    and_(
                        LeaveRequest.end_date >= start_date,
                        LeaveRequest.end_date <= end_date
                    ),
                    # Case 3: New request is contained within existing request
                    and_(
                        LeaveRequest.start_date <= start_date,
                        LeaveRequest.end_date >= end_date
                    )
                )
            )
        )
        
        if exclude_request_id:
            query = query.filter(LeaveRequest.id != exclude_request_id)
        
        return query.all()
    
    def create(self, **kwargs) -> LeaveRequest:
        """Create new leave request."""
        request = LeaveRequest(**kwargs)
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        logger.info(f"Leave request created: {request.id}")
        return request
    
    def update(self, request_id: UUID, **kwargs) -> LeaveRequest:
        """Update leave request."""
        request = self.get_by_id(request_id)
        if not request:
            raise NotFoundException(detail=f"Leave request {request_id} not found")
        
        for key, value in kwargs.items():
            if hasattr(request, key):
                setattr(request, key, value)
        
        self.db.commit()
        self.db.refresh(request)
        logger.info(f"Leave request updated: {request.id}")
        return request
