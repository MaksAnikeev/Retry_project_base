import logging
import uuid
from typing import TYPE_CHECKING

from src.clients.report_service_client import ReportServiceClient
from src.mappers.task_mapper import to_task_api_request
from src.repositories.task_rep import TasksRepository
from src.database.unit_of_work import UnitOfWork
from src.schemas.sync_worker_schemas import SyncStatsSchema
from src.schemas.tasks_schemas import ReportStatus, TaskAPIResponseSchema

if TYPE_CHECKING:
    from src.models import TaskORM


class ReportSyncWorker:
    def __init__(
        self,
        task_repo: TasksRepository,
        report_client: ReportServiceClient,
        uow: UnitOfWork,
        batch_size: int = 50,
    ) -> None:
        self.task_repo = task_repo
        self.report_client = report_client
        self.uow = uow
        self.batch_size = batch_size
        self.logger = logging.getLogger(self.__class__.__name__)

    async def run(self) -> SyncStatsSchema:
        self.logger.info("Starting sync run", extra={"batch_size": self.batch_size})
        stats = SyncStatsSchema(processed=0, updated=0)
        while True:
            pending_tasks = await self._fetch_next_batch()
            if not pending_tasks:
                self.logger.info(
                    "No more pending tasks, sync completed",
                    extra=stats.model_dump(),
                )
                break

            batch_stats = await self._process_batch(pending_tasks)
            stats.processed += batch_stats.processed
            stats.updated += batch_stats.updated
        self.logger.info("Sync run finished", extra=stats.model_dump())
        return stats

    async def _fetch_next_batch(self) -> list[TaskORM]:
        async with self.uow:
            tasks = await self.task_repo.get_tasks_pending_reports(
                limit=self.batch_size,
            )

        self.logger.info(
            "Fetched pending tasks",
            extra={"count": len(tasks)},
        )
        return tasks

    async def _process_batch(self, tasks: list[TaskORM]) -> SyncStatsSchema:
        reports_by_id = await self._fetch_reports(tasks)
        async with self.uow:
            updated_count = await self._enrich_tasks_with_reports(tasks, reports_by_id)

        self.logger.info(
            "Batch processed",
            extra={"batch_size": len(tasks), "updated_count": updated_count},
        )

        return SyncStatsSchema(processed=len(tasks), updated=updated_count)

    async def _fetch_reports(
        self,
        tasks: list[TaskORM],
    ) -> dict[uuid.UUID, TaskAPIResponseSchema]:
        requests = [to_task_api_request(task) for task in tasks]
        reports = await self.report_client.get_reports_batch(requests)
        return {r.task_id: r for r in reports}


    async def _enrich_tasks_with_reports(
        self,
        tasks: list[TaskORM],
        reports_by_id: dict[uuid.UUID, TaskAPIResponseSchema],
    ) -> int:
        updated_count = 0
        for task in tasks:
            report = reports_by_id.get(task.id)
            if report is None:
                self.logger.warning(
                    "Report not returned for task, will retry later",
                    extra={"task_id": str(task.id)},
                )
                continue

            try:
                async with self.uow.session.begin_nested():
                    task.complexity = report.complexity
                    task.estimated_hours = report.estimated_hours
                    task.priority = report.priority
                    task.report_status = ReportStatus.COMPLETED.value
                    await self.uow.session.flush()
                updated_count += 1
            except Exception as e:
                self.logger.error(
                    "Failed to save task, will retry on next run",
                    extra={
                        "task_id": str(task.id),
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
        return updated_count
