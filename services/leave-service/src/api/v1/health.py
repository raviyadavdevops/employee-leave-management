"""Health check endpoint for leave service."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.database import get_db
from src.services.rabbitmq_client import rabbitmq_client
from shared.common.schemas import HealthResponse
from shared.common.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint with database and RabbitMQ checks.
    """
    checks = {}
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        checks["database"] = "unhealthy"
    
    # Check RabbitMQ
    try:
        rabbitmq_healthy = await rabbitmq_client.health_check()
        checks["rabbitmq"] = "healthy" if rabbitmq_healthy else "unhealthy"
    except Exception as e:
        logger.error(f"RabbitMQ health check failed: {str(e)}")
        checks["rabbitmq"] = "unhealthy"
    
    status = "healthy" if all(v == "healthy" for v in checks.values()) else "unhealthy"
    
    return HealthResponse(
        status=status,
        service="leave-service",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
        checks=checks
    )
