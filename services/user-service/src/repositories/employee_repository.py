"""Employee repository for database operations."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.models.employee import Employee
from shared.common.exceptions import NotFoundException, ConflictException, BadRequestException
from shared.common.logging import get_logger

logger = get_logger(__name__)


class EmployeeRepository:
    """Repository for Employee model database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, employee_id: UUID) -> Optional[Employee]:
        """Get employee by ID."""
        return self.db.query(Employee).filter(Employee.id == employee_id).first()
    
    def get_by_email(self, email: str) -> Optional[Employee]:
        """Get employee by email."""
        return self.db.query(Employee).filter(Employee.email == email).first()
    
    def get_team_members(self, manager_id: UUID) -> List[Employee]:
        """
        Get all team members reporting to a manager.
        
        Args:
            manager_id: Manager's user ID
            
        Returns:
            List of Employee objects
        """
        return self.db.query(Employee).filter(Employee.manager_id == manager_id).all()
    
    def create(self, **kwargs) -> Employee:
        """Create new employee."""
        # Validate manager exists if provided
        if kwargs.get('manager_id'):
            manager = self.get_by_id(kwargs['manager_id'])
            if not manager:
                raise BadRequestException(detail=f"Manager with ID {kwargs['manager_id']} not found")
            
            # Prevent self-reference
            if kwargs['id'] == kwargs['manager_id']:
                raise BadRequestException(detail="Employee cannot be their own manager")
        
        employee = Employee(**kwargs)
        
        try:
            self.db.add(employee)
            self.db.commit()
            self.db.refresh(employee)
            logger.info(f"Employee created: {employee.id}")
            return employee
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Employee creation failed: {str(e)}")
            raise ConflictException(detail=f"Employee with email {kwargs.get('email')} already exists")
    
    def update(self, employee_id: UUID, **kwargs) -> Employee:
        """Update employee fields."""
        employee = self.get_by_id(employee_id)
        if not employee:
            raise NotFoundException(detail=f"Employee with ID {employee_id} not found")
        
        # Validate manager if being updated
        if 'manager_id' in kwargs and kwargs['manager_id']:
            if kwargs['manager_id'] == employee_id:
                raise BadRequestException(detail="Employee cannot be their own manager")
            manager = self.get_by_id(kwargs['manager_id'])
            if not manager:
                raise BadRequestException(detail=f"Manager with ID {kwargs['manager_id']} not found")
        
        for key, value in kwargs.items():
            if hasattr(employee, key) and value is not None:
                setattr(employee, key, value)
        
        self.db.commit()
        self.db.refresh(employee)
        logger.info(f"Employee updated: {employee.id}")
        return employee
