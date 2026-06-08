"""Leave type repository."""

from typing import List, Optional
from sqlalchemy.orm import Session

from src.models.leave_type import LeaveType
from shared.common.exceptions import NotFoundException
from shared.common.logging import get_logger

logger = get_logger(__name__)


class LeaveTypeRepository:
    """Repository for LeaveType model."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self, active_only: bool = True) -> List[LeaveType]:
        """Get all leave types."""
        query = self.db.query(LeaveType)
        if active_only:
            query = query.filter(LeaveType.is_active == True)
        return query.all()
    
    def get_by_id(self, leave_type_id: int) -> Optional[LeaveType]:
        """Get leave type by ID."""
        return self.db.query(LeaveType).filter(LeaveType.id == leave_type_id).first()
    
    def get_by_name(self, name: str) -> Optional[LeaveType]:
        """Get leave type by name."""
        return self.db.query(LeaveType).filter(LeaveType.name == name).first()
