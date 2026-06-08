"""
Base event schemas for RabbitMQ messaging.

Provides standardized event structure for event-driven communication.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Literal
from pydantic import BaseModel, Field, UUID4


class BaseEvent(BaseModel):
    """
    Base event schema for all RabbitMQ messages.
    
    All events must inherit from this class to ensure consistent structure.
    """
    
    event_id: UUID4 = Field(
        default_factory=uuid.uuid4,
        description="Unique event identifier for idempotency"
    )
    event_type: str = Field(..., description="Event type identifier (e.g., 'leave_request_created')")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 timestamp when event was created"
    )
    correlation_id: Optional[str] = Field(None, description="Request correlation ID for tracing")
    data: Dict[str, Any] = Field(..., description="Event payload data")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional metadata (source service, version, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "a1b2c3d4-e5f6-4321-abcd-1234567890ab",
                "event_type": "leave_request_created",
                "timestamp": "2026-06-04T12:00:00+00:00",
                "correlation_id": "req_abc123",
                "data": {
                    "leave_request_id": "lr_12345",
                    "employee_id": "emp_67890",
                    "leave_type": "annual",
                    "start_date": "2026-07-01",
                    "end_date": "2026-07-05"
                },
                "metadata": {
                    "source_service": "leave-service",
                    "version": "1.0.0"
                }
            }
        }


class LeaveRequestCreatedEvent(BaseEvent):
    """Event published when a new leave request is created."""
    
    event_type: Literal["leave_request_created"] = "leave_request_created"


class LeaveRequestApprovedEvent(BaseEvent):
    """Event published when a leave request is approved."""
    
    event_type: Literal["leave_request_approved"] = "leave_request_approved"


class LeaveRequestRejectedEvent(BaseEvent):
    """Event published when a leave request is rejected."""
    
    event_type: Literal["leave_request_rejected"] = "leave_request_rejected"


class LeaveBalanceUpdatedEvent(BaseEvent):
    """Event published when employee leave balance is updated."""
    
    event_type: Literal["leave_balance_updated"] = "leave_balance_updated"
