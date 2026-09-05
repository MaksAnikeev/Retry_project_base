import logging
import uuid

from aiokafka.errors import KafkaError

from src.database.unit_of_work import UnitOfWork
from src.kafka.kafka_producer import KafkaProducerClient
from src.mappers.order_mapper import to_order_outbox_schema
from src.mappers.outbox_mapper import to_outboxes_claimed_schema
from src.repositories.outbox_rep import OutboxRepository
from src.schemas.order_schemas import OrderAggregateType, OrderEventType, OrderCreateMessageSchema, OrderHeadersSchema
from src.schemas.outbox_schemas import OutboxClaimedSchema
from src.schemas.sync_worker_schemas import SyncStatsSchema


class OutboxOrderWorker:
    def __init__(
        self,
        outbox_repo: OutboxRepository,
        uow: UnitOfWork,
        kafka_producer: KafkaProducerClient,
        outbox_batch_size: int,
        outbox_max_batch_count: int,
        outbox_max_attempts: int,
        backoff_base_seconds: int,
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
        self.logger.debug("Starting outbox worker run",
                          extra={"batch_size": self.outbox_batch_size})
        stats = SyncStatsSchema(processed=0, updated=0)
        batch_count = 0
        while batch_count < self.outbox_max_batch_count:
            async with self.uow:
                claimed_orms, attempt_id = await self.outbox_repo.claim_messages(
                    limit=self.outbox_batch_size,
                    event_type=OrderEventType.ORDER_CREATED.value,
                    aggregate_type=OrderAggregateType.ORDER.value,
                )
                claimed = to_outboxes_claimed_schema(claimed_orms)
            if not claimed:
                break

            sent, failed = await self._send_batch(claimed)
            if sent:
                async with self.uow:
                    updated_count = await self.outbox_repo.mark_completed(
                        message_ids=[m.id for m in sent],
                        expected_attempt_id=attempt_id,
                    )
                stats.updated += updated_count
            if failed:
                await self._handle_failed(failed, attempt_id)
            stats.processed += len(claimed)
            batch_count += 1
        self.logger.info("Worker run finished", extra=stats.model_dump())
        return stats

    async def _send_batch(
        self,
        messages: list[OutboxClaimedSchema],
    ) -> tuple[list[OutboxClaimedSchema], list[tuple[OutboxClaimedSchema, Exception]]]:
        sent: list[OutboxClaimedSchema] = []
        failed: list[tuple[OutboxClaimedSchema, Exception]] = []

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

    async def _handle_failed(
        self,
        failed: list[tuple[OutboxClaimedSchema, Exception]],
        attempt_id: uuid.UUID) -> None:
        for message, error in failed:
            error_message = f"{type(error).__name__}: {str(error)}"
            await self.outbox_repo.mark_failed_with_retry(
                message_id=message.id,
                error_message=error_message,
                expected_attempt_id=attempt_id,
                max_attempts=self.outbox_max_attempts,
                backoff_base_seconds=self.backoff_base_seconds,
            )

    async def _send_message(self, message: OutboxClaimedSchema) -> None:
        key = str(message.aggregate_id)
        order_payload = to_order_outbox_schema(message.payload)
        order_headers = OrderHeadersSchema(
            event_type=message.event_type or "unknown",
            aggregate_type=message.aggregate_type or "unknown",
            event_id=str(message.id),
        )
        order_message = OrderCreateMessageSchema(
            topic=message.topic,
            key=key,
            payload=order_payload,
            headers=order_headers,
        )

        await self.kafka_producer.send_message(message=order_message)

        self.logger.debug(
            "Message sent to Kafka",
            extra={
                "message_id": str(message.id),
                "topic": message.topic,
                "aggregate_id": str(message.aggregate_id),
            },
        )
