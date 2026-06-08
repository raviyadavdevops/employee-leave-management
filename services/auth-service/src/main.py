"""
FastAPI application for authentication service.

Main application with middleware, exception handlers, and routes.
"""

import os
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.health import router as health_router
from src.api.v1.endpoints.auth import router as auth_router
from shared.common.logging import CorrelationIDMiddleware, get_logger, get_correlation_id
from shared.common.exceptions import BaseAPIException

logger = get_logger(__name__)

# Application environment
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
SERVICE_START_TIME = datetime.now(timezone.utc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Auth service starting up (version {SERVICE_VERSION})")
    yield
    # Shutdown
    logger.info("Auth service shutting down gracefully")


# Create FastAPI app
app = FastAPI(
    title="Employee Leave Management - Auth Service",
    description="Authentication and authorization service",
    version="1.0.0",
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
    lifespan=lifespan
)

# CORS middleware
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Correlation ID middleware
app.add_middleware(CorrelationIDMiddleware)


# Exception handlers
@app.exception_handler(BaseAPIException)
async def api_exception_handler(request: Request, exc: BaseAPIException):
    """
    Handle custom API exceptions.
    
    Args:
        request: FastAPI request
        exc: API exception
        
    Returns:
        JSON response with error details
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "detail": exc.detail,
            "status_code": exc.status_code,
            "correlation_id": get_correlation_id()
        },
        headers=exc.headers
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions.
    
    Args:
        request: FastAPI request
        exc: Exception
        
    Returns:
        JSON response with error details
    """
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "detail": "An unexpected error occurred",
            "status_code": 500,
            "correlation_id": get_correlation_id()
        }
    )


# Include routers
app.include_router(health_router, prefix="", tags=["Health"])
app.include_router(auth_router, prefix="", tags=["Authentication"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "auth-service",
        "version": "1.0.0",
        "status": "running"
    }
