"""RabbitMQ consumer for leave events."""

import os
import json
import asyncio
from typing import Dict, Any
from uuid import UUID
import aio_pika
from aio_pika import IncomingMessage
from sqlalchemy.orm import Session

from src.repositories.notification_repository import NotificationRepository
from src.services.notification_service import NotificationService
from src.database import SessionLocal
from shared.common.logging import get_logger, set_correlation_id, clear_correlation_id

logger = get_logger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://rabbitmq:rabbitmq@localhost:5672/")
EXCHANGE_NAME = "leave_events"
QUEUE_NAME = "notification_queue"


class RabbitMQConsumer:
    """RabbitMQ consumer for processing leave events."""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.queue = None
    
    async def connect(self):
        """Establish connection to RabbitMQ."""
        try:
            self.connection = await aio_pika.connect_robust(RABBITMQ_URL)
            self.channel = await self.connection.channel()
            
            # Set QoS to process one message at a time
            await self.channel.set_qos(prefetch_count=1)
            
            # Declare exchange
            exchange = await self.channel.declare_exchange(
                EXCHANGE_NAME,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            # Declare queue
            self.queue = await self.channel.declare_queue(
                QUEUE_NAME,
                durable=True
            )
            
            # Bind queue to exchange with routing keys
            await self.queue.bind(exchange, routing_key="leave_request_created")
            await self.queue.bind(exchange, routing_key="leave_request_approved")
            await self.queue.bind(exchange, routing_key="leave_request_rejected")
            
            # Configure dead letter queue
            await self.channel.declare_queue(
                f"{QUEUE_NAME}.dlq",
                durable=True
            )
            
            logger.info(f"RabbitMQ consumer connected: {QUEUE_NAME}")
        except Exception as e:
            logger.error(f"Failed to connect RabbitMQ consumer: {str(e)}")
            raise
    
    async def start_consuming(self):
        """Start consuming messages from queue."""
        if not self.queue:
            raise RuntimeError("Consumer not connected. Call connect() first.")
        
        logger.info("Starting to consume messages...")
        await self.queue.consume(self.process_message)
    
    async def process_message(self, message: IncomingMessage):
        """Process incoming RabbitMQ message."""
        async with message.process():
            try:
                # Parse message
                event_data = json.loads(message.body.decode())
                
                # Set correlation ID from message
                correlation_id = event_data.get('correlation_id')
                if correlation_id:
                    set_correlation_id(correlation_id)
                
                logger.info(f"Processing event: {event_data.get('event_type')}")
                
                # Create notification
                await self.create_notification(event_data)
                
                logger.info(f"Event processed successfully: {event_data.get('event_id')}")
                
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}", exc_info=True)
                # Message will be requeued automatically if not acked
                raise
            finally:
                clear_correlation_id()
    
    async def create_notification(self, event_data: Dict[str, Any]):
        """Create notification from event data."""
        db = SessionLocal()
        try:
            service = NotificationService(db)
            
            # Extract event details
            event_id = event_data.get('event_id')
            event_type = event_data.get('event_type')
            data = event_data.get('data', {})
            
            # Route by event type
            if event_type == 'leave_request_created':
                notification = await self.handle_leave_submitted(service, event_id, event_type, data)
            elif event_type == 'leave_request_approved':
                notification = await self.handle_leave_approved(service, event_id, event_type, data)
            elif event_type == 'leave_request_rejected':
                notification = await self.handle_leave_rejected(service, event_id, event_type, data)
            else:
                logger.warning(f"Unknown event type: {event_type}")
                return
            
            # Deliver notification
            if notification:
                await service.deliver_notification(notification.id)
            
        except Exception as e:
            logger.error(f"Failed to create notification: {str(e)}")
            raise
        finally:
            db.close()
    
    async def handle_leave_submitted(
        self,
        service: NotificationService,
        event_id: str,
        event_type: str,
        data: Dict[str, Any]
    ):
        """Handle leave request submitted event - notify manager."""
        recipient_id = data.get('manager_id')  # Notify manager
        
        if not recipient_id:
            logger.warning(f"No manager ID for event {event_id}")
            return None
        
        message = (
            f"New leave request from {data.get('employee_name', 'Employee')}\n"
            f"Type: {data.get('leave_type', 'Unknown')}\n"
            f"Dates: {data.get('start_date')} to {data.get('end_date')}\n"
            f"Days: {data.get('days_requested')}"
        )
        
        notification = service.create_notification(
            event_id=UUID(event_id),
            event_type=event_type,
            recipient_id=UUID(recipient_id),
            message=message
        )
        
        logger.info(f"Created notification for manager {recipient_id}")
        return notification
    
    async def handle_leave_approved(
        self,
        service: NotificationService,
        event_id: str,
        event_type: str,
        data: Dict[str, Any]
    ):
        """Handle leave request approved event - notify employee."""
        recipient_id = data.get('employee_id')  # Notify employee
        
        if not recipient_id:
            logger.warning(f"No employee ID for event {event_id}")
            return None
        
        comment = data.get('comment', '')
        message = (
            f"Your leave request has been APPROVED ✅\n"
            f"Dates: {data.get('start_date')} to {data.get('end_date')}\n"
            f"Approved by: {data.get('approved_by', 'Manager')}"
        )
        
        if comment:
            message += f"\nComment: {comment}"
        
        notification = service.create_notification(
            event_id=UUID(event_id),
            event_type=event_type,
            recipient_id=UUID(recipient_id),
            message=message
        )
        
        logger.info(f"Created notification for employee {recipient_id}")
        return notification
    
    async def handle_leave_rejected(
        self,
        service: NotificationService,
        event_id: str,
        event_type: str,
        data: Dict[str, Any]
    ):
        """Handle leave request rejected event - notify employee with reason."""
        recipient_id = data.get('employee_id')  # Notify employee
        
        if not recipient_id:
            logger.warning(f"No employee ID for event {event_id}")
            return None
        
        reason = data.get('reason', 'No reason provided')
        message = (
            f"Your leave request has been REJECTED ❌\n"
            f"Dates: {data.get('start_date')} to {data.get('end_date')}\n"
            f"Rejected by: {data.get('rejected_by', 'Manager')}\n"
            f"Reason: {reason}"
        )
        
        notification = service.create_notification(
            event_id=UUID(event_id),
            event_type=event_type,
            recipient_id=UUID(recipient_id),
            message=message
        )
        
        logger.info(f"Created notification for employee {recipient_id}")
        return notification
    
    async def disconnect(self):
        """Close RabbitMQ connection."""
        try:
            if self.channel:
                await self.channel.close()
            if self.connection:
                await self.connection.close()
            logger.info("RabbitMQ consumer disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting RabbitMQ consumer: {str(e)}")


# Global consumer instance
rabbitmq_consumer = RabbitMQConsumer()
