"""Calendar and coverage schemas."""

from datetime import date
from uuid import UUID
from pydantic import BaseModel, Field
from typing import List


class CalendarEntry(BaseModel):
    """Calendar entry for a single leave period."""
    
    employee_id: UUID
    employee_name: str
    leave_type: str
    start_date: date
    end_date: date
    status: str


class CoverageWarning(BaseModel):
    """Coverage warning for overlapping leaves."""
    
    date_range: str = Field(description="Date range with coverage issue")
    affected_dates: List[date] = Field(description="List of dates with low coverage")
    employee_count: int = Field(description="Number of employees on leave")
    employees: List[str] = Field(description="Names of employees on leave")
    severity: str = Field(description="warning | critical")


class TeamCalendarResponse(BaseModel):
    """Response schema for team calendar."""
    
    team_size: int
    leave_entries: List[CalendarEntry]
    coverage_warnings: List[CoverageWarning]
