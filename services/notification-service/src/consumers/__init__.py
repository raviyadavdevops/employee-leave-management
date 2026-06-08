"""Consumers for notification service."""

from src.consumers.rabbitmq_consumer import RabbitMQConsumer, rabbitmq_consumer

__all__ = ["RabbitMQConsumer", "rabbitmq_consumer"]
