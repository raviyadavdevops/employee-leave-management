"""Leave balance schemas."""

from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field
from typing import Optional


class LeaveBalanceResponse(BaseModel):
    """Response schema for leave balance."""
    
    id: UUID
    employee_id: UUID
    leave_type_id: int
    leave_type_name: str
    leave_type_display_name: str
    year: int
    total_allocated: Decimal = Field(description="Total leave allocated for the year")
    available: Decimal = Field(description="Available leave (can be used)")
    provisional: Decimal = Field(description="Provisionally booked (pending approval)")
    consumed: Decimal = Field(description="Already consumed leave")
    
    class Config:
        from_attributes = True


class LeaveTypeResponse(BaseModel):
    """Response schema for leave type."""
    
    id: int
    name: str
    display_name: str
    default_allocation: Decimal
    requires_approval: bool
    is_active: bool
    
    class Config:
        from_attributes = True
