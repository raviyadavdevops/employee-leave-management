"""
Pydantic schemas for employee/user service.

Request/response schemas for employee endpoints.
"""

from typing import Optional
from datetime import date
from pydantic import BaseModel, EmailStr, Field, UUID4


class CreateEmployeeRequest(BaseModel):
    """
    Create employee request schema.
    
    Used for POST /api/v1/employees endpoint.
    """
    
    id: UUID4 = Field(..., description="User ID from auth service")
    first_name: str = Field(..., min_length=1, max_length=255, description="Employee first name")
    last_name: str = Field(..., min_length=1, max_length=255, description="Employee last name")
    email: EmailStr = Field(..., description="Employee email address")
    department: Optional[str] = Field(None, max_length=100, description="Employee department")
    manager_id: Optional[UUID4] = Field(None, description="Manager user ID (optional)")
    hire_date: date = Field(..., description="Employment start date")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "a1b2c3d4-e5f6-4321-abcd-1234567890ab",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "department": "Engineering",
                "manager_id": "b2c3d4e5-f6a7-5432-bcde-234567890abc",
                "hire_date": "2025-01-15"
            }
        }


class UpdateEmployeeRequest(BaseModel):
    """
    Update employee request schema.
    """
    
    first_name: Optional[str] = Field(None, min_length=1, max_length=255)
    last_name: Optional[str] = Field(None, min_length=1, max_length=255)
    department: Optional[str] = Field(None, max_length=100)
    manager_id: Optional[UUID4] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "department": "Product Management",
                "manager_id": "c3d4e5f6-a7b8-6543-cdef-34567890abcd"
            }
        }


class EmployeeResponse(BaseModel):
    """
    Employee response schema.
    """
    
    id: UUID4 = Field(..., description="Employee ID")
    first_name: str = Field(..., description="Employee first name")
    last_name: str = Field(..., description="Employee last name")
    email: EmailStr = Field(..., description="Employee email")
    department: Optional[str] = Field(None, description="Employee department")
    manager_id: Optional[UUID4] = Field(None, description="Manager ID")
    hire_date: date = Field(..., description="Employment start date")
    full_name: str = Field(..., description="Employee full name")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "a1b2c3d4-e5f6-4321-abcd-1234567890ab",
                "first_name": "John",
                "last_name": "Doe",
                "full_name": "John Doe",
                "email": "john.doe@example.com",
                "department": "Engineering",
                "manager_id": "b2c3d4e5-f6a7-5432-bcde-234567890abc",
                "hire_date": "2025-01-15"
            }
        }
