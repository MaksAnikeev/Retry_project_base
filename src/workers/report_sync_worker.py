import asyncio
import logging
import uuid
from typing import TYPE_CHECKING

import circuitbreaker

from src.clients.report_service_client import ReportServiceClient
from src.config import settings
from src.exceptions import ExternalServiceUnavailableException
from src.mappers.task_mapper import to_task_api_request
from src.repositories.task_rep import TasksRepository
from src.repositories.unit_of_work import UnitOfWork
from src.schemas.sync_worker_schemas import SyncStatsSchema
from src.schemas.tasks_schemas import ReportStatus, TaskAPIResponseSchema

if TYPE_CHECKING:
    from src.models import TaskORM


class ReportSyncWorker:

    max_consecutive_failures = settings.MAX_CONSECUTIVE_FAILURES
    failure_backoff_seconds = settings.FAILURE_BACKOFF_SECONDS

    cb_wait_second = settings.CB_WAIT_SECONDS
    max_cb_retries = settings.MAX_CB_RETRIES

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
        self._consecutive_failures = 0
        self._cb_retries = 0

    async def run(self) -> SyncStatsSchema:
        self.logger.info(
            "Starting sync run",
            extra={"batch_size": self.batch_size},
        )

        stats = {"processed": 0, "updated": 0}

        try:
            while True:
                async with self.uow:
                    pending_tasks = await self.task_repo.get_tasks_pending_reports(
                        limit=self.batch_size,
                    )

                if not pending_tasks:
                    self.logger.info(
                        "No more pending tasks, sync completed",
                        extra=stats,
                    )
                    break

                batch_stats = await self._process_batch(pending_tasks)
                if batch_stats is not None:
                    stats["processed"] += batch_stats.processed
                    stats["updated"] += batch_stats.updated

                if self._consecutive_failures >= self.max_consecutive_failures:
                    self.logger.error(
                        "Max consecutive failures reached, aborting sync",
                        extra={
                            "consecutive_failures": self._consecutive_failures,
                            "max_failures": self.max_consecutive_failures,
                        },
                    )
                    break

                if self._cb_retries >= self.max_cb_retries:
                    self.logger.error(
                        "Circuit breaker stayed open too long, aborting sync",
                        extra={
                            "cb_retries": self._cb_retries,
                            "max_cb_retries": self.max_cb_retries,
                            "waited_minutes": self._cb_retries * self.cb_wait_second // 60,
                        },
                    )
                    break

        except Exception as e:
            self.logger.error(
                "Sync run crashed",
                extra={"error": str(e), **stats},
                exc_info=True,
            )
            raise

        self.logger.info("Sync run finished", extra=stats)
        return SyncStatsSchema(
            processed=stats["processed"],
            updated=stats["updated"],
        )

    async def _process_batch(self, tasks: list["TaskORM"]) -> SyncStatsSchema | None:
        self.logger.info(
            "Processing batch",
            extra={"tasks_count": len(tasks)},
        )
        reports = await self._fetch_reports(tasks)
        if reports is None:
            return None

        self._consecutive_failures = 0
        self._cb_retries = 0

        updated_count = self._apply_reports_to_tasks(tasks, reports)

        if updated_count > 0:
            async with self.uow:
                await self.uow.session.flush()

        self.logger.info(
            "Batch processed",
            extra={
                "batch_size": len(tasks),
                "updated_count": updated_count,
            },
        )
        return SyncStatsSchema(
            processed=len(tasks),
            updated=updated_count,
        )

    async def _fetch_reports(
        self,
        tasks: list[TaskORM],
    ) -> dict[uuid.UUID, TaskAPIResponseSchema] | None:
        try:
            requests = [to_task_api_request(task) for task in tasks]
            reports = await self.report_client.get_reports_batch(requests)
            return {r.task_id: r for r in reports}

        except ExternalServiceUnavailableException as e:
            self._consecutive_failures += 1

            self.logger.warning(
                "External service unavailable",
                extra={
                    "error": str(e),
                    "consecutive_failures": self._consecutive_failures,
                    "max_failures": self.max_consecutive_failures,
                },
            )

            await asyncio.sleep(self.failure_backoff_seconds)
            return None

        except circuitbreaker.CircuitBreakerError as e:
            self._cb_retries += 1
            self.logger.warning(
                "Circuit breaker is OPEN, waiting before retry",
                extra={
                    "error": str(e),
                    "cb_retries": self._cb_retries,
                    "max_cb_retries": self.max_cb_retries,
                    "wait_seconds": self.cb_wait_second,
                },
            )
            await asyncio.sleep(self.cb_wait_second)
            return None

    def _apply_reports_to_tasks(
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

            task.complexity = report.complexity
            task.estimated_hours = report.estimated_hours
            task.priority = report.priority
            task.report_status = ReportStatus.COMPLETED.value
            updated_count += 1

        return updated_count
