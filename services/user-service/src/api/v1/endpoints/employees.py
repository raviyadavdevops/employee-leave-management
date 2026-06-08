"""Employee endpoints for user service."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from src.database import get_db
from src.services.employee_service import EmployeeService
from src.schemas.employee import EmployeeResponse, CreateEmployeeRequest
from shared.common.auth import get_current_user, get_current_manager
from shared.common.schemas import UserContext
from shared.common.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/employees", tags=["Employees"])


@router.get("/me", response_model=EmployeeResponse)
async def get_current_employee_profile(
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's employee profile.
    
    Returns the authenticated employee's profile information.
    """
    service = EmployeeService(db)
    return service.get_current_employee(current_user)


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: UUID,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get employee by ID.
    
    Authorization:
    - Employees can only view their own profile
    - Managers can view their team members' profiles
    """
    service = EmployeeService(db)
    return service.get_employee(employee_id, current_user)


@router.get("/team/members", response_model=List[EmployeeResponse])
async def get_team_members(
    current_user: UserContext = Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    """
    Get team members (managers only).
    
    Returns list of employees reporting to the current manager.
    """
    service = EmployeeService(db)
    return service.get_team_members(current_user)


@router.post("/", response_model=EmployeeResponse, status_code=201)
async def create_employee(
    request: CreateEmployeeRequest,
    current_user: UserContext = Depends(get_current_manager),
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Create new employee (managers only).
    
    Automatically allocates leave balances via leave-service.
    Note: In production, this should also create the auth user first.
    """
    token = authorization.replace("Bearer ", "")
    
    service = EmployeeService(db)
    return await service.create_employee(request, current_user, token)
