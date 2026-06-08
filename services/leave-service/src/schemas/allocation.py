"""Allocation schemas for leave balances."""

from datetime import date
from uuid import UUID
from pydantic import BaseModel, Field
from typing import List
from decimal import Decimal


class AllocateBalancesRequest(BaseModel):
    """Request schema for allocating leave balances."""
    
    employee_id: UUID = Field(description="Employee ID to allocate balances for")
    hire_date: date = Field(description="Employee hire date")
    year: int = Field(default=None, description="Year to allocate for (default: current year)")


class AllocationResponse(BaseModel):
    """Response schema for balance allocation."""
    
    employee_id: UUID
    year: int
    allocations: List[dict] = Field(description="List of allocated leave types with amounts")
    message: str
