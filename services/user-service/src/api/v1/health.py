"""Health check endpoint for user service."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.database import get_db
from shared.common.schemas import HealthResponse
from shared.common.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint with database connectivity check."""
    checks = {}
    
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        checks["database"] = "unhealthy"
    
    status = "healthy" if all(v == "healthy" for v in checks.values()) else "unhealthy"
    
    return HealthResponse(
        status=status,
        service="user-service",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
        checks=checks
    )
