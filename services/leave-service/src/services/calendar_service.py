"""Calendar service for team coverage visualization."""

from typing import List
from uuid import UUID
from datetime import date, timedelta
from collections import defaultdict
from sqlalchemy.orm import Session

from src.repositories.leave_request_repository import LeaveRequestRepository
from src.services.user_service_client import user_service_client
from src.schemas.calendar import CalendarEntry, CoverageWarning, TeamCalendarResponse
from shared.common.schemas import UserContext
from shared.common.exceptions import ForbiddenException, BadRequestException
from shared.common.logging import get_logger

logger = get_logger(__name__)


class CalendarService:
    """Service for team calendar and coverage analysis."""
    
    def __init__(self, db: Session):
        self.db = db
        self.request_repo = LeaveRequestRepository(db)
    
    async def get_team_calendar(
        self,
        current_user: UserContext,
        token: str,
        start_date: date = None,
        end_date: date = None
    ) -> TeamCalendarResponse:
        """
        Get team calendar with coverage warnings.
        
        Shows approved leave and identifies coverage gaps.
        """
        if not current_user.is_manager():
            raise ForbiddenException(detail="Only managers can view team calendar")
        
        # Fetch team members
        try:
            team_member_ids = await user_service_client.get_team_members(
                current_user.user_id,
                token
            )
        except Exception as e:
            logger.error(f"Failed to fetch team members: {str(e)}")
            raise BadRequestException(detail="Failed to fetch team members")
        
        if not team_member_ids:
            return TeamCalendarResponse(
                team_size=0,
                leave_entries=[],
                coverage_warnings=[]
            )
        
        # Fetch approved leave requests
        requests = self.request_repo.get_team_requests(team_member_ids, status="approved")
        
        # Filter by date range if provided
        if start_date or end_date:
            requests = [
                req for req in requests
                if (not start_date or req.end_date >= start_date) and
                   (not end_date or req.start_date <= end_date)
            ]
        
        # Build calendar entries
        entries = [
            CalendarEntry(
                employee_id=req.employee_id,
                employee_name=str(req.employee_id),  # TODO: Fetch from user service
                leave_type="Unknown",  # TODO: Fetch leave type
                start_date=req.start_date,
                end_date=req.end_date,
                status=req.status
            )
            for req in requests
        ]
        
        # Calculate coverage warnings
        warnings = self._calculate_coverage_warnings(team_member_ids, requests)
        
        return TeamCalendarResponse(
            team_size=len(team_member_ids),
            leave_entries=entries,
            coverage_warnings=warnings
        )
    
    def _calculate_coverage_warnings(
        self,
        team_member_ids: List[UUID],
        requests: List
    ) -> List[CoverageWarning]:
        """
        Calculate coverage warnings for overlapping leave periods.
        
        Warning: >30% of team on leave
        Critical: >50% of team on leave
        """
        team_size = len(team_member_ids)
        if team_size == 0:
            return []
        
        # Map dates to employees on leave
        date_coverage = defaultdict(set)
        
        for req in requests:
            current_date = req.start_date
            while current_date <= req.end_date:
                date_coverage[current_date].add(req.employee_id)
                current_date += timedelta(days=1)
        
        # Find coverage gaps
        warnings = []
        current_warning = None
        
        for leave_date in sorted(date_coverage.keys()):
            employees_on_leave = date_coverage[leave_date]
            coverage_pct = len(employees_on_leave) / team_size
            
            if coverage_pct > 0.3:  # More than 30% on leave
                severity = "critical" if coverage_pct > 0.5 else "warning"
                
                if current_warning and current_warning["severity"] == severity:
                    # Extend current warning
                    current_warning["affected_dates"].append(leave_date)
                    current_warning["employees"].update(employees_on_leave)
                else:
                    # Save previous warning
                    if current_warning:
                        warnings.append(self._build_warning(current_warning, team_size))
                    
                    # Start new warning
                    current_warning = {
                        "severity": severity,
                        "affected_dates": [leave_date],
                        "employees": set(employees_on_leave)
                    }
            else:
                # End current warning
                if current_warning:
                    warnings.append(self._build_warning(current_warning, team_size))
                    current_warning = None
        
        # Don't forget last warning
        if current_warning:
            warnings.append(self._build_warning(current_warning, team_size))
        
        return warnings
    
    def _build_warning(self, warning_data: dict, team_size: int) -> CoverageWarning:
        """Build coverage warning from accumulated data."""
        affected_dates = warning_data["affected_dates"]
        employees = warning_data["employees"]
        
        if len(affected_dates) == 1:
            date_range = str(affected_dates[0])
        else:
            date_range = f"{affected_dates[0]} to {affected_dates[-1]}"
        
        return CoverageWarning(
            date_range=date_range,
            affected_dates=affected_dates,
            employee_count=len(employees),
            employees=[str(emp) for emp in employees],  # TODO: Fetch names
            severity=warning_data["severity"]
        )
