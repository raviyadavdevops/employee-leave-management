"""Notification repository with idempotency checks."""

from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.models.notification import Notification, NotificationStatus
from shared.common.logging import get_logger

logger = get_logger(__name__)


class NotificationRepository:
    """Repository for Notification model with idempotency support."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_event_id(self, event_id: UUID) -> Optional[Notification]:
        """Get notification by event ID (for idempotency check)."""
        return self.db.query(Notification).filter(Notification.event_id == event_id).first()
    
    def create(
        self,
        event_id: UUID,
        event_type: str,
        recipient_id: UUID,
        message: str
    ) -> Optional[Notification]:
        """
        Create notification with idempotency.
        
        Returns None if notification already exists for this event_id.
        """
        # Check if already processed
        existing = self.get_by_event_id(event_id)
        if existing:
            logger.info(f"Notification for event {event_id} already exists, skipping")
            return None
        
        notification = Notification(
            event_id=event_id,
            event_type=event_type,
            recipient_id=recipient_id,
            message=message,
            status=NotificationStatus.PENDING
        )
        
        try:
            self.db.add(notification)
            self.db.commit()
            self.db.refresh(notification)
            logger.info(f"Notification created: {notification.id}")
            return notification
        except IntegrityError:
            # Race condition: another process created it
            self.db.rollback()
            logger.warning(f"Notification for event {event_id} created by another process")
            return None
    
    def mark_sent(self, notification_id: UUID) -> None:
        """Mark notification as sent."""
        notification = self.db.query(Notification).filter(Notification.id == notification_id).first()
        if notification:
            notification.status = NotificationStatus.SENT
            from datetime import datetime, timezone
            notification.sent_at = datetime.now(timezone.utc)
            self.db.commit()
            logger.info(f"Notification marked as sent: {notification_id}")
    
    def mark_failed(self, notification_id: UUID, error_message: str, retry_count: int) -> None:
        """Mark notification as failed."""
        notification = self.db.query(Notification).filter(Notification.id == notification_id).first()
        if notification:
            notification.status = NotificationStatus.FAILED
            notification.error_message = error_message
            notification.retry_count = str(retry_count)
            self.db.commit()
            logger.error(f"Notification marked as failed: {notification_id}")
