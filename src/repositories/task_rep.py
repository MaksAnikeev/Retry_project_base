from typing import Any

from sqlalchemy import Row, or_, select, update
from sqlalchemy.orm import selectinload

from src.models import TaskORM
from src.repositories.base import BaseRepository
from src.schemas.tasks_schemas import TaskGetSchema


class TasksRepository(BaseRepository[TaskORM, TaskGetSchema]):
    model = TaskORM

    async def get_one_or_none_with_relationship(self, **filters: Any) -> TaskORM | None:
        query = select(self.model).filter_by(**filters).options(selectinload(self.model.user))
        query_result = await self.session.execute(query)
        return query_result.scalars().one_or_none()

    async def delete_bulk_by_conditions(self, conditions: list) -> int:
        if not conditions:
            return 0
        stmt = (
            update(self.model)
            .where(or_(*conditions))
            .values(is_deleted=True)
        )
        result = await self.session.execute(stmt)
        return result.rowcount
