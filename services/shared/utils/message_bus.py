"""Message bus utilities for inter-service communication"""
import json
import logging
from typing import Any, Callable, Dict, Optional
import aio_pika
from aio_pika import Message, ExchangeType
from aio_pika.abc import AbstractConnection, AbstractChannel, AbstractExchange

logger = logging.getLogger(__name__)


class MessageBus:
    """RabbitMQ message bus for async communication between services"""

    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url
        self.connection: Optional[AbstractConnection] = None
        self.channel: Optional[AbstractChannel] = None
        self.exchange: Optional[AbstractExchange] = None

    async def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()

            # Declare exchange for topic-based routing
            self.exchange = await self.channel.declare_exchange(
                "encheres_events",
                ExchangeType.TOPIC,
                durable=True
            )
            logger.info("Connected to RabbitMQ message bus")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self):
        """Close connection to RabbitMQ"""
        if self.connection:
            await self.connection.close()
            logger.info("Disconnected from RabbitMQ")

    async def publish(
        self,
        routing_key: str,
        message: Dict[str, Any],
        priority: int = 0
    ):
        """
        Publish a message to the exchange

        Args:
            routing_key: Topic routing key (e.g., "lot.price.updated")
            message: Message payload as dictionary
            priority: Message priority (0-9)
        """
        if not self.exchange:
            await self.connect()

        try:
            message_body = json.dumps(message).encode()
            await self.exchange.publish(
                Message(
                    body=message_body,
                    content_type="application/json",
                    priority=priority,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key=routing_key
            )
            logger.debug(f"Published message to {routing_key}: {message}")
        except Exception as e:
            logger.error(f"Failed to publish message to {routing_key}: {e}")
            raise

    async def subscribe(
        self,
        queue_name: str,
        routing_keys: list[str],
        callback: Callable
    ):
        """
        Subscribe to messages matching routing keys

        Args:
            queue_name: Name of the queue to create
            routing_keys: List of routing patterns (e.g., ["lot.*.updated", "sale.created"])
            callback: Async callback function to handle messages
        """
        if not self.channel or not self.exchange:
            await self.connect()

        try:
            # Declare queue
            queue = await self.channel.declare_queue(
                queue_name,
                durable=True,
                arguments={"x-max-priority": 10}
            )

            # Bind queue to exchange with routing keys
            for routing_key in routing_keys:
                await queue.bind(self.exchange, routing_key=routing_key)
                logger.info(f"Bound queue {queue_name} to {routing_key}")

            # Start consuming messages
            await queue.consume(callback)
            logger.info(f"Started consuming from queue {queue_name}")
        except Exception as e:
            logger.error(f"Failed to subscribe to queue {queue_name}: {e}")
            raise


# Event types (routing keys)
class EventTypes:
    """Standard event routing keys"""

    # User events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"

    # Sale events
    SALE_CREATED = "sale.created"
    SALE_UPDATED = "sale.updated"
    SALE_STATUS_CHANGED = "sale.status.changed"

    # Lot events
    LOT_CREATED = "lot.created"
    LOT_UPDATED = "lot.updated"
    LOT_PRICE_UPDATED = "lot.price.updated"
    LOT_FAVORITED = "lot.favorited"
    LOT_UNFAVORITED = "lot.unfavorited"

    # Alert events
    ALERT_CREATED = "alert.created"
    ALERT_TRIGGERED = "alert.triggered"

    # Notification events
    NOTIFICATION_SEND = "notification.send"

    # Scraper events
    SCRAPER_JOB_STARTED = "scraper.job.started"
    SCRAPER_JOB_COMPLETED = "scraper.job.completed"
    SCRAPER_JOB_FAILED = "scraper.job.failed"
