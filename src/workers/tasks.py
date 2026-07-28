import asyncio
import logging

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.clients.report_service_client import create_report_client
from src.config import settings
from src.repositories.task_rep import TasksRepository
from src.database.unit_of_work import UnitOfWork
from src.schemas.sync_worker_schemas import SyncStatsSchema
from src.workers.celery_app import celery_instance
from src.workers.report_sync_worker import ReportSyncWorker

logger = logging.getLogger(__name__)


@celery_instance.task(
    bind=True,
    acks_late=True,
    reject_on_worker_lost=True,
)
def sync_reports_task(self) -> dict:
    try:
        stats = asyncio.run(_run_worker())
        return stats.model_dump()

    except Exception as e:
        logger.error(
            "sync_reports_task failed",
            extra={"error": str(e)},
            exc_info=True,
        )
        raise


async def _run_worker() -> SyncStatsSchema:
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
