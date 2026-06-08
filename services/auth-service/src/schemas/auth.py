"""
Pydantic schemas for authentication service.

Request/response schemas for auth endpoints.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, UUID4


class LoginRequest(BaseModel):
    """
    Login request schema.
    
    Used for POST /api/v1/auth/login endpoint.
    """
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (minimum 8 characters)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "john.doe@example.com",
                "password": "SecurePassword123!"
            }
        }


class TokenResponse(BaseModel):
    """
    Token response schema.
    
    Returned after successful login or token refresh.
    """
    
    access_token: str = Field(..., description="JWT access token (short-lived)")
    refresh_token: str = Field(..., description="JWT refresh token (long-lived)")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    expires_in: int = Field(..., description="Access token expiration time in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 900
            }
        }


class RefreshTokenRequest(BaseModel):
    """
    Refresh token request schema.
    
    Used for POST /api/v1/auth/refresh endpoint.
    """
    
    refresh_token: str = Field(..., description="JWT refresh token")
    
    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class LogoutRequest(BaseModel):
    """
    Logout request schema.
    
    Used for POST /api/v1/auth/logout endpoint.
    """
    
    refresh_token: str = Field(..., description="JWT refresh token to blacklist")
    
    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class RegisterUserRequest(BaseModel):
    """
    User registration request schema.
    
    Internal use only (for creating test users or admin operations).
    """
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (minimum 8 characters)")
    role: str = Field(..., description="User role: 'employee' or 'manager'")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "jane.smith@example.com",
                "password": "SecurePassword456!",
                "role": "employee"
            }
        }


class UserResponse(BaseModel):
    """
    User response schema (without sensitive data).
    """
    
    id: UUID4 = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email address")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="Account active status")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "a1b2c3d4-e5f6-4321-abcd-1234567890ab",
                "email": "john.doe@example.com",
                "role": "employee",
                "is_active": True
            }
        }
