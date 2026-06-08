"""Notification model."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, Text, Boolean, DateTime, Enum as SQLAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class NotificationStatus(str, Enum):
    """Notification delivery status."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class Notification(Base):
    """Notification model. Table: notifications.notifications"""
    
    __tablename__ = "notifications"
    __table_args__ = {'schema': 'notifications'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True, comment="Event ID for idempotency")
    event_type = Column(String(100), nullable=False, comment="Type of event that triggered notification")
    recipient_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="User ID to notify")
    message = Column(Text, nullable=False, comment="Notification message")
    status = Column(
        SQLAEnum(
            NotificationStatus,
            name='notification_status',
            schema='notifications',
            values_callable=lambda enum_cls: [member.value for member in enum_cls]
        ),
        default=NotificationStatus.PENDING,
        nullable=False,
        index=True
    )
    sent_at = Column(DateTime(timezone=True), nullable=True, comment="When notification was sent")
    error_message = Column(Text, nullable=True, comment="Error message if delivery failed")
    retry_count = Column(String(10), default='0', nullable=False, comment="Number of delivery attempts")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, event_type={self.event_type}, status={self.status})>"
