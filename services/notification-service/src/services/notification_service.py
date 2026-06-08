"""Notification service business logic."""

import asyncio
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from src.models.notification import Notification, NotificationStatus
from src.repositories.notification_repository import NotificationRepository
from shared.common.logging import get_logger

logger = get_logger(__name__)


class NotificationService:
    """Service for notification management and delivery."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = NotificationRepository(db)
    
    def create_notification(
        self,
        event_id: UUID,
        event_type: str,
        recipient_id: UUID,
        message: str
    ) -> Optional[Notification]:
        """
        Create notification with idempotency.
        
        Returns None if notification already exists for this event.
        """
        return self.repo.create(
            event_id=event_id,
            event_type=event_type,
            recipient_id=recipient_id,
            message=message
        )
    
    async def deliver_notification(
        self,
        notification_id: UUID,
        max_retries: int = 3
    ) -> bool:
        """
        Deliver notification with retry logic.
        
        For MVP: Simulates email delivery via console logging.
        In production: Integrate with email service (SendGrid, SES, etc.)
        
        Returns True if delivery successful.
        """
        notification = self.db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            logger.error(f"Notification {notification_id} not found")
            return False
        
        retry_count = 0
        backoff_delay = 1  # seconds
        
        while retry_count < max_retries:
            try:
                # Simulate email delivery
                logger.info(
                    f"📧 NOTIFICATION DELIVERY:\n"
                    f"  To: {notification.recipient_id}\n"
                    f"  Type: {notification.event_type}\n"
                    f"  Message: {notification.message}\n"
                    f"  Event ID: {notification.event_id}"
                )
                
                # In production, call email API here
                # await send_email(notification.recipient_id, notification.message)
                
                # Mark as sent
                self.repo.mark_sent(notification_id)
                logger.info(f"Notification {notification_id} delivered successfully")
                return True
                
            except Exception as e:
                retry_count += 1
                error_msg = f"Delivery failed (attempt {retry_count}/{max_retries}): {str(e)}"
                logger.error(error_msg)
                
                if retry_count >= max_retries:
                    # Mark as failed after max retries
                    self.repo.mark_failed(notification_id, error_msg, retry_count)
                    return False
                
                # Exponential backoff
                await asyncio.sleep(backoff_delay)
                backoff_delay *= 2
        
        return False
    
    def get_user_notifications(
        self,
        recipient_id: UUID,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """
        Get notifications for user with optional filtering.
        """
        query = self.db.query(Notification).filter(Notification.recipient_id == recipient_id)
        
        if status:
            try:
                status_enum = NotificationStatus(status)
                query = query.filter(Notification.status == status_enum)
            except ValueError:
                logger.warning(f"Invalid status filter: {status}")
        
        query = query.order_by(Notification.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        return query.all()
