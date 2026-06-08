"""
Base exception classes for Employee Leave Management System.

Provides a hierarchy of HTTP-aware exceptions with structured error responses.
"""

from typing import Any, Dict, Optional


class BaseAPIException(Exception):
    """
    Base exception class for all API errors.
    
    Attributes:
        status_code: HTTP status code
        detail: Error message
        headers: Optional HTTP headers
    """
    
    def __init__(
        self,
        detail: str,
        status_code: int = 500,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Initialize API exception.
        
        Args:
            detail: Error message
            status_code: HTTP status code (default 500)
            headers: Optional HTTP headers
        """
        self.detail = detail
        self.status_code = status_code
        self.headers = headers
        super().__init__(detail)
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary for JSON serialization.
        
        Returns:
            Dictionary with error details
        """
        return {
            "error": self.__class__.__name__,
            "detail": self.detail,
            "status_code": self.status_code,
        }


class UnauthorizedException(BaseAPIException):
    """
    Exception raised when authentication is required but not provided or invalid.
    
    HTTP Status: 401 Unauthorized
    """
    
    def __init__(
        self,
        detail: str = "Authentication required",
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(detail=detail, status_code=401, headers=headers)


class ForbiddenException(BaseAPIException):
    """
    Exception raised when authenticated user lacks permission for the operation.
    
    HTTP Status: 403 Forbidden
    """
    
    def __init__(
        self,
        detail: str = "Insufficient permissions",
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(detail=detail, status_code=403, headers=headers)


class NotFoundException(BaseAPIException):
    """
    Exception raised when requested resource is not found.
    
    HTTP Status: 404 Not Found
    """
    
    def __init__(
        self,
        detail: str = "Resource not found",
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(detail=detail, status_code=404, headers=headers)


class BadRequestException(BaseAPIException):
    """
    Exception raised for invalid request data or parameters.
    
    HTTP Status: 400 Bad Request
    """
    
    def __init__(
        self,
        detail: str = "Bad request",
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(detail=detail, status_code=400, headers=headers)


class ConflictException(BaseAPIException):
    """
    Exception raised when request conflicts with current resource state.
    
    HTTP Status: 409 Conflict
    """
    
    def __init__(
        self,
        detail: str = "Resource conflict",
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(detail=detail, status_code=409, headers=headers)


class ValidationException(BaseAPIException):
    """
    Exception raised for data validation failures.
    
    HTTP Status: 422 Unprocessable Entity
    """
    
    def __init__(
        self,
        detail: str = "Validation error",
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(detail=detail, status_code=422, headers=headers)
