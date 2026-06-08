"""Event schemas for notification service."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from typing import Optional, Dict, Any


class LeaveSubmittedEvent(BaseModel):
    """Event when leave request is submitted."""
    
    event_id: UUID
    event_type: str
    request_id: UUID
    employee_id: UUID
    employee_name: str
    leave_type: str
    start_date: str
    end_date: str
    days_requested: str
    manager_id: Optional[UUID]
    correlation_id: Optional[str]


class LeaveApprovedEvent(BaseModel):
    """Event when leave request is approved."""
    
    event_id: UUID
    event_type: str
    request_id: UUID
    employee_id: UUID
    start_date: str
    end_date: str
    approved_by: UUID
    comment: Optional[str]
    correlation_id: Optional[str]


class LeaveRejectedEvent(BaseModel):
    """Event when leave request is rejected."""
    
    event_id: UUID
    event_type: str
    request_id: UUID
    employee_id: UUID
    start_date: str
    end_date: str
    rejected_by: UUID
    reason: str
    correlation_id: Optional[str]
