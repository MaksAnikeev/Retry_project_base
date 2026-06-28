from sqlalchemy import or_, update, select

from src.models import TaskORM
from src.repositories.base import BaseRepository
from src.schemas.tasks_schemas import TaskGetSchema


class TasksRepository(BaseRepository[TaskORM, TaskGetSchema]):
    model = TaskORM

    async def get_tasks_pending_reports(self, limit: int = 50) -> list[TaskORM]:
        stmt = (
            select(TaskORM)
            .where(TaskORM.is_report_pending == True)
            .order_by(TaskORM.created_at)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
