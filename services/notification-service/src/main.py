"""FastAPI application for notification service with background consumer."""

import os
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.database import get_db
from src.consumers.rabbitmq_consumer import rabbitmq_consumer
from src.api.v1.endpoints.notifications import router as notifications_router
from shared.common.schemas import HealthResponse
from shared.common.logging import get_logger, CorrelationIDMiddleware
from shared.common.auth import get_current_user
from shared.common.exceptions import BaseAPIException

logger = get_logger(__name__)

APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with RabbitMQ consumer."""
    # Startup
    logger.info("Notification service starting up")

    async def start_consumer_with_retry():
        while True:
            try:
                await rabbitmq_consumer.connect()
                await rabbitmq_consumer.start_consuming()
                logger.info("RabbitMQ consumer started")
                return
            except Exception as e:
                logger.error(f"Failed to start RabbitMQ consumer: {str(e)}")
                await asyncio.sleep(5)

    asyncio.create_task(start_consumer_with_retry())
    
    yield
    
    # Shutdown
    logger.info("Notification service shutting down")
    try:
        await rabbitmq_consumer.disconnect()
    except Exception as e:
        logger.error(f"Error during consumer disconnect: {str(e)}")


app = FastAPI(
    title="Employee Leave Management - Notification Service",
    description="Notification service for leave events",
    version="1.0.0",
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(CorrelationIDMiddleware)

# Include routers
app.include_router(notifications_router, prefix="", tags=["Notifications"])


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    checks = {}
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        checks["database"] = "unhealthy"
    
    # Check RabbitMQ consumer
    try:
        if rabbitmq_consumer.connection and not rabbitmq_consumer.connection.is_closed:
            checks["rabbitmq"] = "healthy"
        else:
            checks["rabbitmq"] = "unhealthy"
    except Exception as e:
        logger.error(f"RabbitMQ health check failed: {str(e)}")
        checks["rabbitmq"] = "unhealthy"
    
    status = "healthy" if all(v == "healthy" for v in checks.values()) else "unhealthy"
    
    return HealthResponse(
        status=status,
        service="notification-service",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
        checks=checks
    )


@app.get("/")
async def root():
    return {"service": "notification-service", "version": "1.0.0", "status": "running"}
