import asyncio
import logging

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.clients.report_http_client import create_report_client
from src.config import get_settings
from src.repositories.task_rep import TasksRepository
from src.schemas.sync_worker_schemas import SyncStatsSchema
from src.workers.celery_app import celery_instance
from src.workers.report_sync_worker import ReportSyncWorker

logger = logging.getLogger(__name__)

settings = get_settings()


@celery_instance.task(
    name="src.workers.tasks.sync_reports_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def sync_reports_task(self) -> dict:
    logger.info("Starting sync_reports_task")

    try:
        stats = asyncio.run(_run_worker())
        logger.info("sync_reports_task completed", extra=stats.model_dump())
        return stats.model_dump()

    except RuntimeError as e:
        if "attached to a different loop" in str(e):
            logger.warning(
                "Event loop error detected, will retry",
                extra={"error": str(e)},
            )
            raise self.retry(exc=e)
        raise

    except Exception as e:
        logger.error(
            "sync_reports_task failed",
            extra={"error": str(e)},
            exc_info=True,
        )
        raise self.retry(exc=e)


async def _run_worker() -> SyncStatsSchema:
    engine = create_async_engine(
        settings.DATABASE_URL_asyncpg,
        pool_pre_ping=True,
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    session = session_factory()
    report_client = create_report_client()

    try:
        task_repo = TasksRepository(session=session)
        worker = ReportSyncWorker(
            task_repo=task_repo,
            report_client=report_client,
            batch_size=50,
        )
        return await worker.run()
    finally:
        await session.close()
        await engine.dispose()
        await report_client.close()