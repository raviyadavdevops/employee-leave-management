"""
Common Pydantic schemas for API responses.

Provides standardized response schemas used across all microservices.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """
    Standard error response schema.
    
    Used for all API error responses across services.
    """
    
    error: str = Field(..., description="Error type or exception class name")
    detail: str = Field(..., description="Human-readable error message")
    status_code: int = Field(..., description="HTTP status code")
    correlation_id: Optional[str] = Field(None, description="Request correlation ID for tracing")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "NotFoundException",
                "detail": "Employee with ID 123 not found",
                "status_code": 404,
                "correlation_id": "a1b2c3d4-e5f6-4321-abcd-1234567890ab"
            }
        }


class MessageResponse(BaseModel):
    """
    Standard success message response schema.
    
    Used for operations that return a simple success message.
    """
    
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Optional additional data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Leave request submitted successfully",
                "data": {"request_id": "req_12345"}
            }
        }


class HealthResponse(BaseModel):
    """
    Health check response schema.
    
    Used by all services for health endpoints.
    """
    
    status: str = Field(..., description="Health status: 'healthy' or 'unhealthy'")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    checks: Dict[str, str] = Field(default_factory=dict, description="Individual health checks")
    uptime_seconds: float = Field(default=0.0, description="Service uptime in seconds")
    service: str = Field(..., description="Service name")
    version: str = Field(default="1.0.0", description="Service version")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    checks: Optional[Dict[str, str]] = Field(None, description="Component health checks (database, queue, etc.)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "auth-service",
                "version": "1.0.0",
                "timestamp": "2026-06-04T12:00:00Z",
                "checks": {
                    "database": "healthy",
                    "redis": "healthy"
                }
            }
        }


class PaginatedResponse(BaseModel):
    """
    Paginated response wrapper.
    
    Used for list endpoints that support pagination.
    """
    
    items: list[Any] = Field(..., description="List of items for current page")
    total: int = Field(..., description="Total number of items across all pages")
    page: int = Field(default=1, ge=1, description="Current page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 150,
                "page": 1,
                "page_size": 20,
                "total_pages": 8
            }
        }
