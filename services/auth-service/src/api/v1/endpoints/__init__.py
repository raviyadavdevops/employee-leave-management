"""API v1 endpoints package."""

from src.api.v1.endpoints.auth import router as auth_router

__all__ = ["auth_router"]
