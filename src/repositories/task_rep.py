from sqlalchemy import select

from src.models import TaskORM
from src.repositories.base import BaseRepository
from src.schemas.tasks_schemas import TaskGetSchema, ReportStatus


class TasksRepository(BaseRepository[TaskORM, TaskGetSchema]):
    model = TaskORM

    async def get_tasks_pending_reports(self, limit: int = 50) -> list[TaskORM]:
        stmt = (
            select(TaskORM)
            .where(TaskORM.report_status == ReportStatus.PENDING.value)
            .order_by(TaskORM.created_at)
            .with_for_update(skip_locked=True)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
