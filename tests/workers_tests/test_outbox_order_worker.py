from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

from aiokafka.errors import KafkaError
from httpx import AsyncClient
from sqlalchemy import select, update

from src.config import settings
from src.database.unit_of_work import UnitOfWork
from src.models import OutboxORM
from src.repositories.outbox_rep import OutboxRepository
from src.workers.outbox_order_worker import OutboxOrderWorker


def make_mock_send_message():
    async def mock_send_message(topic, value, key, headers):
        product_name = value.get('product_name', '')

        if product_name == "Удочка":
            return
        elif product_name == "Леска":
            raise KafkaError(f"Simulated error for {product_name}")
        else:
            return
    return mock_send_message


async def test_outbox_order_worker(
    setup_db,
    ac: AsyncClient,
    async_session_factory_null_pull,
):
    payload = [
        {
            "user_id": "de662447-4321-4922-9f88-16150f295c99",
            "product_name": "Удочка",
            "price": 1500000,
            "quantity": 2
        },
        {
            "user_id": "c54e6396-d7d2-4d53-bece-51c91990fa5b",
            "product_name": "Леска",
            "price": 100000,
            "quantity": 5
        }
    ]
    response = await ac.post("/orders", json=payload)
    assert response.status_code == 200
    async with async_session_factory_null_pull() as session:
        stmt = select(OutboxORM)
        result = await session.execute(stmt)
        outbox_entries = result.scalars().all()
        for outbox in outbox_entries:
            assert outbox.event_type == "OrderCreated"
            assert "product_name" in outbox.payload
            assert outbox.status == "pending"

    mock_kafka_producer = AsyncMock()
    mock_kafka_producer.send_message.side_effect = make_mock_send_message()
    mock_kafka_producer.close = AsyncMock()

    async with async_session_factory_null_pull() as session:
        uow = UnitOfWork(session=session)
        outbox_repo = OutboxRepository(session=session)

        worker = OutboxOrderWorker(
            outbox_repo=outbox_repo,
            kafka_producer=mock_kafka_producer,
            uow=uow,
            outbox_batch_size=settings.OUTBOX_BATCH_SIZE,
            outbox_max_batch_count=settings.OUTBOX_MAX_BATCH_COUNT,
            outbox_max_attempts=settings.OUTBOX_MAX_ATTEMPTS,
        )
        try:
            stats = await worker.run()
        finally:
            await mock_kafka_producer.close()

        assert stats.processed > 0, "Воркер должен был обработать задачи"

        async with async_session_factory_null_pull() as check_session:
            stmt = select(OutboxORM)
            result = await check_session.execute(stmt)
            outbox_entries = result.scalars().all()
            for outbox in outbox_entries:
                if outbox.payload.get('product_name') == "Удочка":
                    assert outbox.status == "completed"
                    assert outbox.sent_at is not None
                    assert outbox.last_error is None
                if outbox.payload.get('product_name') == "Леска":
                    assert outbox.status == "pending"
                    assert outbox.attempts >= 1
                    assert outbox.last_error is not None
                    assert outbox.next_attempt_at is not None

        assert mock_kafka_producer.send_message.call_count >= 2
        assert mock_kafka_producer.close.called


async def mock_always_fail(*args, **kwargs):
    raise KafkaError("Always fails")


async def test_outbox_max_attempts_marks_failed(
    ac: AsyncClient,
    async_session_factory_null_pull,
):
    payload = [{
        "user_id": "de662447-4321-4922-9f88-16150f295c99",
        "product_name": "Фейл-тест",
        "price": 100000,
        "quantity": 1,
    }]
    await ac.post("/orders", json=payload)

    mock_producer = AsyncMock()
    mock_producer.send_message.side_effect = mock_always_fail
    mock_producer.close = AsyncMock()

    for attempt in range(settings.OUTBOX_MAX_ATTEMPTS):
        async with async_session_factory_null_pull() as session:
            past_time = datetime.now(UTC) - timedelta(hours=1)
            await session.execute(
                update(OutboxORM)
                .where(OutboxORM.payload["product_name"].as_string() == "Фейл-тест")
                .values(next_attempt_at=past_time)
            )
            await session.commit()

            worker = OutboxOrderWorker(
                outbox_repo=OutboxRepository(session=session),
                kafka_producer=mock_producer,
                uow=UnitOfWork(session=session),
                outbox_batch_size=settings.OUTBOX_BATCH_SIZE,
                outbox_max_batch_count=settings.OUTBOX_MAX_BATCH_COUNT,
                outbox_max_attempts=settings.OUTBOX_MAX_ATTEMPTS,
            )
            await worker.run()

    async with async_session_factory_null_pull() as check_session:
        stmt = select(OutboxORM).where(
            OutboxORM.payload["product_name"].as_string() == "Фейл-тест"
        )
        result = await check_session.execute(stmt)
        outbox = result.scalar_one_or_none()

        assert outbox is not None
        assert outbox.status == "failed"
        assert outbox.attempts == settings.OUTBOX_MAX_ATTEMPTS
        assert outbox.next_attempt_at is None
