from datetime import datetime, UTC, timedelta
import logging

from aiokafka.errors import KafkaError

from src.schemas.outbox_schemas import OrderEventType, OrderAggregateType
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
        backoff_base_seconds: int = 60,
    ) -> None:
        self.outbox_repo = outbox_repo
        self.uow = uow
        self.kafka_producer = kafka_producer
        self.outbox_batch_size = outbox_batch_size
        self.outbox_max_batch_count = outbox_max_batch_count
        self.outbox_max_attempts = outbox_max_attempts
        self.backoff_base_seconds = backoff_base_seconds

        self.logger = logging.getLogger(self.__class__.__name__)

    async def run(self) -> SyncStatsSchema:
        self.logger.debug("Starting outbox worker run", extra={"batch_size": self.outbox_batch_size})
        stats = SyncStatsSchema(processed=0, updated=0)
        batch_count = 0
        while batch_count < self.outbox_max_batch_count:
            async with self.uow:
                claimed = await self.outbox_repo.claim_messages(
                    limit=self.outbox_batch_size,
                    event_type=OrderEventType.ORDER_CREATED.value,
                    aggregate_type=OrderAggregateType.ORDER.value,
                )
            if not claimed:
                break

            sent, failed = await self._send_batch(claimed)
            if sent:
                async with self.uow:
                    for msg in sent:
                        msg.status = OutboxStatus.COMPLETED
                        msg.sent_at = datetime.now(UTC)
                        msg.last_error = None
                stats.updated += len(sent)
            if failed:
                async with self.uow:
                    await self._handle_failed(failed)
            stats.processed += len(claimed)
            batch_count += 1
        self.logger.info("Worker run finished", extra=stats.model_dump())
        return stats

    async def _send_batch(
        self,
        messages: list[OutboxORM],
    ) -> tuple[list[OutboxORM], list[tuple[OutboxORM, Exception]]]:
        sent: list[OutboxORM] = []
        failed: list[tuple[OutboxORM, Exception]] = []

        for message in messages:
            try:
                await self._send_message(message)
                sent.append(message)

            except KafkaError as e:
                self.logger.warning(
                    "Kafka error during send, will retry",
                    extra={
                        "message_id": str(message.id),
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
                failed.append((message, e))

            except (ConnectionError, TimeoutError, OSError) as e:
                self.logger.warning(
                    "Network error during send, will retry",
                    extra={
                        "message_id": str(message.id),
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
                failed.append((message, e))
        return sent, failed

    async def _handle_failed(self, failed: list[tuple[OutboxORM, Exception]]) -> None:
        now = datetime.now(UTC)

        for message, error in failed:
            error_message = f"{type(error).__name__}: {str(error)}"
            message.attempts += 1
            message.last_error = error_message[:2000]

            if message.attempts >= self.outbox_max_attempts:
                message.status = OutboxStatus.FAILED
                message.next_attempt_at = None
            else:
                delay = self.backoff_base_seconds * (2 ** (message.attempts - 1))
                message.status = OutboxStatus.PENDING
                message.next_attempt_at = now + timedelta(seconds=delay)

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
