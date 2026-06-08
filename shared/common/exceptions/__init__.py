"""Common exception classes for Employee Leave Management System."""

from shared.common.exceptions.base import (
    BaseAPIException,
    UnauthorizedException,
    ForbiddenException,
    NotFoundException,
    BadRequestException,
    ConflictException,
    ValidationException,
)

__all__ = [
    "BaseAPIException",
    "UnauthorizedException",
    "ForbiddenException",
    "NotFoundException",
    "BadRequestException",
    "ConflictException",
    "ValidationException",
]
