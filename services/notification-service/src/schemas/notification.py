"""Notification schemas."""

from uuid import UUID
from pydantic import BaseModel
from typing import Optional


class NotificationResponse(BaseModel):
    """Response schema for notification."""
    
    id: UUID
    event_id: UUID
    event_type: str
    recipient_id: UUID
    message: str
    status: str
    sent_at: Optional[str]
    error_message: Optional[str]
    retry_count: str
    created_at: str
    
    class Config:
        from_attributes = True
