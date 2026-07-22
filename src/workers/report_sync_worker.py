import logging
import uuid
from typing import TYPE_CHECKING

import circuitbreaker

from src.clients.report_service_client import ReportServiceClient
from src.exceptions import ExternalServiceUnavailableException
from src.exceptions.external_service import ExternalServiceClientException
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
        max_batch_count: int = 3,
    ) -> None:
        self.task_repo = task_repo
        self.report_client = report_client
        self.uow = uow
        self.batch_size = batch_size
        self.max_batch_count = max_batch_count
        self.logger = logging.getLogger(self.__class__.__name__)

    async def run(self) -> SyncStatsSchema:
        self.logger.debug("Starting sync run", extra={"batch_size": self.batch_size})
        stats = SyncStatsSchema(processed=0, updated=0)
        batch_count = 0
        while batch_count < self.max_batch_count:
            try:
                pending_tasks = await self._fetch_next_batch()
                if not pending_tasks:
                    break

                batch_stats = await self._process_batch(pending_tasks)
                stats.processed += batch_stats.processed
                stats.updated += batch_stats.updated
                batch_count += 1

            except ExternalServiceClientException as e:
                self.logger.warning(
                    "Batch skipped due to data mismatch, continuing to next batch",
                    extra={"batch_number": batch_count + 1, "error": str(e)},
                )
                batch_count += 1
                continue
            except ExternalServiceUnavailableException as e:
                self.logger.error(
                    "External service unavailable, stopping sync run",
                    extra={"batch_number": batch_count + 1, "error": str(e)},
                )
                break
            except circuitbreaker.CircuitBreakerError as e:
                self.logger.error(
                    "Circuit breaker is OPEN - service temporarily unavailable",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                    exc_info=False,
                )
                break
        self.logger.info("Sync run finished", extra=stats.model_dump())
        return stats

    async def _fetch_next_batch(self) -> list[TaskORM]:
        async with self.uow:
            tasks = await self.task_repo.get_tasks_pending_reports(
                limit=self.batch_size,
            )
        return tasks

    async def _process_batch(self, tasks: list[TaskORM]) -> SyncStatsSchema:
        reports_by_id = await self._fetch_reports(tasks)
        async with self.uow:
            updated_count = await self._enrich_tasks_with_reports(tasks, reports_by_id)

        self.logger.debug(
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
        skipped_task_ids = []
        for task in tasks:
            report = reports_by_id.get(task.id)
            if report is None:
                skipped_task_ids.append(str(task.id))
                continue

            task.complexity = report.complexity
            task.estimated_hours = report.estimated_hours
            task.priority = report.priority
            task.report_status = ReportStatus.COMPLETED.value
            updated_count += 1

        if skipped_task_ids:
            self.logger.warning(
                "Tasks skipped due to missing reports",
                extra={
                    "skipped_count": len(skipped_task_ids),
                    "sample_skipped_task_ids": skipped_task_ids[:5],
                },
            )
        if updated_count > 0:
            await self.uow.session.flush()

        return updated_count

