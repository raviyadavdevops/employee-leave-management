"""API v1 endpoints package."""

from src.api.v1.endpoints.notifications import router as notifications_router

__all__ = ["notifications_router"]
