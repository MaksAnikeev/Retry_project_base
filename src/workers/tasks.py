import asyncio
import logging

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.clients.report_service_client import create_report_client
from src.config import settings
from src.database.unit_of_work import UnitOfWork
from src.kafka.kafka_producer import KafkaProducerClient
from src.repositories.outbox_rep import OutboxRepository
from src.repositories.task_rep import TasksRepository
from src.schemas.sync_worker_schemas import SyncStatsSchema
from src.workers.celery_app import celery_instance
from src.workers.outbox_order_worker import OutboxOrderWorker
from src.workers.report_sync_worker import ReportSyncWorker

logger = logging.getLogger(__name__)


@celery_instance.task(
    bind=True,
    acks_late=True,
    reject_on_worker_lost=True,
)
def sync_reports_task(self) -> dict:
    stats = asyncio.run(_run_report_worker())
    return stats.model_dump()


async def _run_report_worker() -> SyncStatsSchema:
    engine = None
    session = None
    report_client = None
    try:
        engine = create_async_engine(
            settings.DATABASE_URL_asyncpg,
            pool_pre_ping=True,
        )
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        session = session_factory()
        report_client = create_report_client()
        uow = UnitOfWork(session=session)
        task_repo = TasksRepository(session=session)
        worker = ReportSyncWorker(
            task_repo=task_repo,
            report_client=report_client,
            uow=uow,
            batch_size=settings.BATCH_SIZE,
            max_batch_count=settings.MAX_BATCH_COUNT,
        )
        return await worker.run()
    finally:
        if report_client is not None:
            await report_client.close()
        if session is not None:
            await session.close()
        if engine is not None:
            await engine.dispose()


@celery_instance.task(
    bind=True,
    acks_late=True,
    reject_on_worker_lost=True,
)
def send_outbox_order(self) -> dict:
    stats = asyncio.run(_run_outbox_worker())
    return stats.model_dump()


async def _run_outbox_worker() -> SyncStatsSchema:
    engine = None
    session = None
    try:
        engine = create_async_engine(
            settings.DATABASE_URL_asyncpg,
            pool_pre_ping=True,
        )
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        session = session_factory()
        uow = UnitOfWork(session=session)
        outbox_repo = OutboxRepository(session=session)
        kafka_producer = KafkaProducerClient(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
        async with kafka_producer.lifespan():
            worker = OutboxOrderWorker(
                outbox_repo=outbox_repo,
                kafka_producer=kafka_producer,
                uow=uow,
                outbox_batch_size=settings.OUTBOX_BATCH_SIZE,
                outbox_max_batch_count=settings.OUTBOX_MAX_BATCH_COUNT,
                outbox_max_attempts=settings.OUTBOX_MAX_ATTEMPTS,
            )
            return await worker.run()
    finally:
        if session is not None:
            await session.close()
        if engine is not None:
            await engine.dispose()
