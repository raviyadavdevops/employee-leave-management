"""API v1 endpoints package."""

from src.api.v1.endpoints.employees import router as employees_router

__all__ = ["employees_router"]
