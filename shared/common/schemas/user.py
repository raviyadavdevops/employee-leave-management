"""
User and role schemas for authentication and authorization.

Provides shared schemas for user identity and role-based access control.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, UUID4


class UserRole(str, Enum):
    """
    User role enumeration.
    
    Defines the two roles in the system:
    - EMPLOYEE: Can manage their own leave requests
    - MANAGER: Can manage their own leave + approve/reject team leave requests
    """
    
    EMPLOYEE = "employee"
    MANAGER = "manager"


class TokenPayload(BaseModel):
    """
    JWT token payload schema.
    
    Represents the claims stored in JWT access tokens.
    """
    
    sub: UUID4 = Field(..., description="Subject (user ID)")
    email: str = Field(..., description="User email address")
    role: UserRole = Field(..., description="User role")
    exp: Optional[int] = Field(None, description="Expiration timestamp (Unix epoch)")
    iat: Optional[int] = Field(None, description="Issued at timestamp (Unix epoch)")
    type: str = Field(default="access", description="Token type: 'access' or 'refresh'")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sub": "a1b2c3d4-e5f6-4321-abcd-1234567890ab",
                "email": "john.doe@example.com",
                "role": "employee",
                "exp": 1717502400,
                "iat": 1717501500,
                "type": "access"
            }
        }


class UserContext(BaseModel):
    """
    User context for authenticated requests.
    
    Injected into request handlers via dependency injection.
    """
    
    user_id: UUID4 = Field(..., description="Authenticated user ID")
    email: str = Field(..., description="User email address")
    role: UserRole = Field(..., description="User role")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "a1b2c3d4-e5f6-4321-abcd-1234567890ab",
                "email": "john.doe@example.com",
                "role": "employee"
            }
        }
    
    def is_manager(self) -> bool:
        """Check if user has manager role."""
        return self.role == UserRole.MANAGER
    
    def is_employee(self) -> bool:
        """Check if user has employee role."""
        return self.role == UserRole.EMPLOYEE
