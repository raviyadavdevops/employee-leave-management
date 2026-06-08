"""FastAPI application for user service."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.health import router as health_router
from src.api.v1.endpoints.employees import router as employees_router
from shared.common.logging import CorrelationIDMiddleware, get_logger, get_correlation_id
from shared.common.exceptions import BaseAPIException

logger = get_logger(__name__)

APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("User service starting up")
    yield
    logger.info("User service shutting down")


app = FastAPI(
    title="Employee Leave Management - User Service",
    description="User and employee management service",
    version="1.0.0",
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
    lifespan=lifespan
)

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(CorrelationIDMiddleware)


@app.exception_handler(BaseAPIException)
async def api_exception_handler(request: Request, exc: BaseAPIException):
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


app.include_router(health_router, prefix="", tags=["Health"])
app.include_router(employees_router, prefix="", tags=["Employees"])


@app.get("/")
async def root():
    return {"service": "user-service", "version": "1.0.0", "status": "running"}
