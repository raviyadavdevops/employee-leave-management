"""Leave type model."""

from sqlalchemy import Column, String, Integer, Numeric, Boolean

from src.models.base import Base


class LeaveType(Base):
    """Leave type model. Table: leaves.leave_types"""
    
    __tablename__ = "leave_types"
    __table_args__ = {'schema': 'leaves'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, comment="Leave type name (e.g., 'annual', 'sick')")
    display_name = Column(String(100), nullable=False, comment="User-friendly name")
    default_allocation = Column(Numeric(5, 2), nullable=False, comment="Default days allocated per year")
    requires_approval = Column(Boolean, default=True, nullable=False, comment="Whether requests require manager approval")
    is_active = Column(Boolean, default=True, nullable=False)
    
    def __repr__(self) -> str:
        return f"<LeaveType(id={self.id}, name={self.name})>"
