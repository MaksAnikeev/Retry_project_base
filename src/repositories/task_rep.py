import uuid

from sqlalchemy import select

from src.models import TaskORM
from src.repositories.base import BaseRepository
from src.schemas.tasks_schemas import ReportStatus


class TasksRepository(BaseRepository[TaskORM]):
    model = TaskORM

    async def get_tasks_pending_reports(
        self,
        limit: int = 50,
        cursor_id: uuid.UUID | None = None,
    ) -> list[TaskORM]:
        stmt = (
            select(self.model)
            .where(self.model.report_status == ReportStatus.PENDING.value)
            .order_by(self.model.id)
            .with_for_update(skip_locked=True)
            .limit(limit)
        )
        if cursor_id is not None:
            stmt = stmt.where(self.model.id > cursor_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
