"""RabbitMQ client for publishing leave events."""

import os
import json
from typing import Dict, Any, Optional
import aio_pika
from aio_pika import Message, DeliveryMode, ExchangeType

from shared.common.schemas.events import BaseEvent
from shared.common.logging import get_logger, get_correlation_id

logger = get_logger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://rabbitmq:rabbitmq@localhost:5672/")
EXCHANGE_NAME = "leave_events"


class RabbitMQClient:
    """RabbitMQ client for publishing events."""
    
    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None
    
    async def connect(self):
        """Establish connection to RabbitMQ."""
        try:
            self.connection = await aio_pika.connect_robust(RABBITMQ_URL)
            self.channel = await self.connection.channel()
            
            # Declare exchange for leave events
            self.exchange = await self.channel.declare_exchange(
                EXCHANGE_NAME,
                ExchangeType.TOPIC,
                durable=True
            )
            
            logger.info(f"RabbitMQ connected: {EXCHANGE_NAME}")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise
    
    async def disconnect(self):
        """Close RabbitMQ connection."""
        try:
            if self.channel:
                await self.channel.close()
            if self.connection:
                await self.connection.close()
            logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {str(e)}")
    
    async def publish_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        routing_key: Optional[str] = None
    ) -> None:
        """
        Publish event to RabbitMQ.
        
        Args:
            event_type: Event type identifier
            data: Event payload data
            routing_key: Optional routing key (defaults to event_type)
        """
        if not self.exchange:
            raise RuntimeError("RabbitMQ not connected. Call connect() first.")
        
        # Create event with correlation ID from current context
        event = BaseEvent(
            event_type=event_type,
            data=data,
            correlation_id=get_correlation_id(),
            metadata={
                "source_service": "leave-service",
                "version": "1.0.0"
            }
        )
        
        # Serialize to JSON
        message_body = event.model_dump_json().encode()
        
        # Create message
        message = Message(
            body=message_body,
            delivery_mode=DeliveryMode.PERSISTENT,
            content_type="application/json",
            correlation_id=event.correlation_id or "",
            message_id=str(event.event_id)
        )
        
        # Publish with routing key
        routing_key = routing_key or event_type
        await self.exchange.publish(message, routing_key=routing_key)
        
        logger.info(f"Event published: {event_type} (routing_key={routing_key})")
    
    async def health_check(self) -> bool:
        """Check if RabbitMQ connection is healthy."""
        try:
            if (
                not self.connection
                or self.connection.is_closed
                or not self.channel
                or self.channel.is_closed
            ):
                # Startup order can cause initial connect to fail. Retry lazily
                # during health checks so service recovers without restart.
                await self.connect()

            if not self.connection or self.connection.is_closed:
                return False
            if not self.channel or self.channel.is_closed:
                return False
            return True
        except Exception as e:
            logger.error(f"RabbitMQ health check failed: {str(e)}")
            return False


# Global RabbitMQ client instance
rabbitmq_client = RabbitMQClient()
