"""Leave request schemas."""

from datetime import date
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum


class LeaveRequestStatus(str, Enum):
    """Leave request status values."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class CreateLeaveRequestRequest(BaseModel):
    """Request schema for creating leave request."""
    
    leave_type_id: int = Field(description="ID of leave type")
    start_date: date = Field(description="Leave start date")
    end_date: date = Field(description="Leave end date")
    reason: str = Field(min_length=1, max_length=500, description="Reason for leave")
    
    @field_validator('end_date')
    @classmethod
    def validate_dates(cls, end_date, info):
        """Validate end_date is after or equal to start_date."""
        start_date = info.data.get('start_date')
        if start_date and end_date < start_date:
            raise ValueError("end_date must be after or equal to start_date")
        return end_date


class LeaveRequestResponse(BaseModel):
    """Response schema for leave request."""
    
    id: UUID
    employee_id: UUID
    leave_type_id: int
    leave_type_name: str
    start_date: date
    end_date: date
    days_requested: Decimal
    reason: str
    status: LeaveRequestStatus
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[str] = None
    review_comment: Optional[str] = None
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class UpdateLeaveRequestStatusRequest(BaseModel):
    """Request schema for updating leave request status (managers only)."""
    
    status: LeaveRequestStatus = Field(description="New status")
    review_comment: Optional[str] = Field(None, max_length=500, description="Review comment")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, status):
        """Only approved/rejected allowed for manager updates."""
        if status not in [LeaveRequestStatus.APPROVED, LeaveRequestStatus.REJECTED]:
            raise ValueError("Status must be 'approved' or 'rejected'")
        return status
