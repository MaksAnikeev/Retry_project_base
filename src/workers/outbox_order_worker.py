import datetime
import logging
from datetime import UTC, datetime, timedelta

from aiokafka.errors import KafkaError

from src.config import settings
from src.database.unit_of_work import UnitOfWork
from src.kafka.kafka_producer import KafkaProducerClient
from src.models import OutboxORM
from src.repositories.outbox_rep import OutboxRepository
from src.schemas.outbox_schemas import OutboxStatus
from src.schemas.sync_worker_schemas import SyncStatsSchema


class OutboxOrderWorker:
    def __init__(
        self,
        outbox_repo: OutboxRepository,
        uow: UnitOfWork,
        kafka_producer: KafkaProducerClient,
        outbox_batch_size: int = 50,
        outbox_max_batch_count: int = 3,
        outbox_max_attempts: int = 3,
    ) -> None:
        self.outbox_repo = outbox_repo
        self.uow = uow
        self.kafka_producer = kafka_producer
        self.outbox_batch_size = outbox_batch_size
        self.outbox_max_batch_count = outbox_max_batch_count
        self.outbox_max_attempts = outbox_max_attempts

        self.logger = logging.getLogger(self.__class__.__name__)

    async def run(self) -> SyncStatsSchema:
        self.logger.debug("Starting outbox worker run", extra={"batch_size": self.outbox_batch_size})
        stats = SyncStatsSchema(processed=0, updated=0)
        batch_count = 0
        cursor_id = None
        while batch_count < self.outbox_max_batch_count:
            try:
                async with self.uow:
                    order_messages = await self.outbox_repo.get_pending_order_messages(
                        limit=self.outbox_batch_size,
                        cursor_id=cursor_id,
                        event_type=settings.ORDER_EVENT_TYPE,
                        aggregate_type=settings.ORDER_AGGREGATE_TYPE,
                    )
                    if not order_messages:
                        break

                    batch_stats = await self._process_batch(order_messages)
                    stats.processed += batch_stats.processed
                    stats.updated += batch_stats.updated
                    batch_count += 1

                    cursor_id = order_messages[-1].id

            except Exception as e:
                self.logger.exception(
                    "Unexpected error in outbox worker",
                    extra={
                        "stats": stats.model_dump(),
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                    exc_info=False,
                )
                raise

        self.logger.info("Worker run finished", extra=stats.model_dump())
        return stats

    async def _process_batch(self, messages: list[OutboxORM]) -> SyncStatsSchema:
        sent_count = 0
        for message in messages:
            try:
                await self._send_message(message)
                message.status = OutboxStatus.COMPLETED.value
                message.sent_at = datetime.now(UTC)
                message.last_error = None
                sent_count += 1

            except Exception as e:
                await self._handle_send_error(message, e)
        await self.uow.session.flush()
        return SyncStatsSchema(processed=len(messages), updated=sent_count)


    async def _send_message(self, message: OutboxORM) -> None:
        key = str(message.aggregate_id)

        headers = {
            "event-type": message.event_type or "unknown",
            "aggregate-type": message.aggregate_type or "unknown",
            "event-id": str(message.id),
        }

        await self.kafka_producer.send_message(
            topic=message.topic,
            value=message.payload,
            key=key,
            headers=headers,
        )

        self.logger.debug(
            "Message sent to Kafka",
            extra={
                "message_id": str(message.id),
                "topic": message.topic,
                "aggregate_id": str(message.aggregate_id),
            },
        )

    async def _handle_send_error(self, message: OutboxORM, error: Exception) -> None:
        error_message = f"{type(error).__name__}: {str(error)}"

        if isinstance(error, KafkaError):
            self.logger.warning(
                "Kafka error during message send",
                extra={
                    "message_id": str(message.id),
                    "error": error_message,
                    "attempts": message.attempts + 1,
                },
            )
        await self._mark_as_failed(
            message=message,
            max_attempts=self.outbox_max_attempts,
            error_message=error_message
        )

    async def _mark_as_failed(
        self,
        message: OutboxORM,
        max_attempts: int,
        error_message: str,
        backoff_base_seconds: int = 60,
    ) -> None:
        message.attempts += 1
        message.last_error = error_message[:2000]

        if message.attempts >= max_attempts:
            message.status = OutboxStatus.FAILED.value
            message.next_attempt_at = None
        else:
            delay = backoff_base_seconds * (2 ** (message.attempts - 1))
            message.next_attempt_at = datetime.now(UTC) + timedelta(seconds=delay)
        await self.uow.session.flush()
