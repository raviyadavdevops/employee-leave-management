"""Employee service business logic."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from src.repositories.employee_repository import EmployeeRepository
from src.schemas.employee import CreateEmployeeRequest, UpdateEmployeeRequest, EmployeeResponse
from src.services.leave_service_client import leave_service_client
from shared.common.schemas import UserContext
from shared.common.exceptions import NotFoundException, ForbiddenException
from shared.common.logging import get_logger

logger = get_logger(__name__)


class EmployeeService:
    """Service for employee management with data scoping."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = EmployeeRepository(db)
    
    def get_employee(self, employee_id: UUID, current_user: UserContext) -> EmployeeResponse:
        """
        Get employee by ID with authorization check.
        
        Employees can only view their own profile.
        Managers can view their team members' profiles.
        """
        employee = self.repo.get_by_id(employee_id)
        if not employee:
            raise NotFoundException(detail=f"Employee with ID {employee_id} not found")
        
        # Authorization: employees can only see their own data
        if not current_user.is_manager():
            if employee.id != current_user.user_id:
                raise ForbiddenException(detail="You can only access your own employee profile")
        else:
            # Managers can see their team members
            # For now, allow all access for managers (in production, check team membership)
            pass
        
        return EmployeeResponse(
            id=employee.id,
            first_name=employee.first_name,
            last_name=employee.last_name,
            email=employee.email,
            department=employee.department,
            manager_id=employee.manager_id,
            hire_date=employee.hire_date,
            full_name=employee.full_name
        )
    
    def get_current_employee(self, current_user: UserContext) -> EmployeeResponse:
        """Get current user's employee profile."""
        return self.get_employee(current_user.user_id, current_user)
    
    def get_team_members(self, current_user: UserContext) -> List[EmployeeResponse]:
        """
        Get team members (for managers only).
        
        Returns list of employees reporting to current user.
        """
        if not current_user.is_manager():
            raise ForbiddenException(detail="Only managers can view team members")
        
        team = self.repo.get_team_members(current_user.user_id)
        
        return [
            EmployeeResponse(
                id=emp.id,
                first_name=emp.first_name,
                last_name=emp.last_name,
                email=emp.email,
                department=emp.department,
                manager_id=emp.manager_id,
                hire_date=emp.hire_date,
                full_name=emp.full_name
            )
            for emp in team
        ]
    
    async def create_employee(
        self,
        request: CreateEmployeeRequest,
        current_user: UserContext,
        token: str
    ) -> EmployeeResponse:
        """
        Create new employee with automatic leave balance allocation.
        
        Steps:
        1. Create employee record
        2. Call leave-service to allocate balances
        3. Log warning if allocation fails (don't rollback)
        """
        if not current_user.is_manager():
            raise ForbiddenException(detail="Only managers can create employees")
        
        # 1. Create employee
        employee = self.repo.create(
            id=request.id,
            first_name=request.first_name,
            last_name=request.last_name,
            email=request.email,
            department=request.department,
            manager_id=request.manager_id,
            hire_date=request.hire_date
        )
        
        # 2. Allocate leave balances
        try:
            success = await leave_service_client.allocate_balances(
                employee.id,
                str(request.hire_date),
                token
            )
            if not success:
                logger.warning(f"Failed to allocate balances for employee {employee.id}")
        except Exception as e:
            logger.error(f"Error allocating balances: {str(e)}")
            # Don't fail employee creation
        
        return EmployeeResponse(
            id=employee.id,
            first_name=employee.first_name,
            last_name=employee.last_name,
            email=employee.email,
            department=employee.department,
            manager_id=employee.manager_id,
            hire_date=employee.hire_date,
            full_name=employee.full_name
        )
