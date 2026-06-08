"""Notification endpoints."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.database import get_db
from src.services.notification_service import NotificationService
from src.schemas.notification import NotificationResponse
from shared.common.auth import get_current_user
from shared.common.schemas import UserContext
from shared.common.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])


@router.get("/me", response_model=List[NotificationResponse])
async def get_my_notifications(
    status: Optional[str] = Query(None, description="Filter by status: pending, sent, failed"),
    limit: int = Query(50, ge=1, le=100, description="Number of notifications to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's notifications.
    
    Supports pagination and filtering by delivery status.
    """
    service = NotificationService(db)
    notifications = service.get_user_notifications(
        current_user.user_id,
        status=status,
        limit=limit,
        offset=offset
    )
    
    return [
        NotificationResponse(
            id=n.id,
            event_id=n.event_id,
            event_type=n.event_type,
            recipient_id=n.recipient_id,
            message=n.message,
            status=n.status.value,
            sent_at=n.sent_at.isoformat() if n.sent_at else None,
            error_message=n.error_message,
            retry_count=n.retry_count,
            created_at=n.created_at.isoformat()
        )
        for n in notifications
    ]
