from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.exceptions import ObjectNotFoundException
from src.models import TasksORM
from src.repositories.base import BaseRepository
from src.repositories.mappers.mappers import TaskDataMapper
from src.repositories.utils import check_safe_filters
from src.schemas.tasks_schemas import TaskUserGetSchemas


class TasksRepository(BaseRepository):
    model = TasksORM
    mapper = TaskDataMapper

    async def get_one_or_none_with_relship(self, **filters) -> BaseModel:
        safe_filters = self._get_safe_filters(filters)
        check_safe_filters(safe_filters)
        query = select(self.model).filter_by(**safe_filters)
        query_result = await self.session.execute(query)
        result = query_result.scalars().one_or_none()
        if not result:
            raise ObjectNotFoundException
        query = (
            select(self.model)
            .filter_by(**safe_filters)
            .options(selectinload(self.model.user))  # type: ignore
        )
        query_result = await self.session.execute(query)
        result = query_result.scalars().one_or_none()
        return TaskUserGetSchemas.model_validate(result, from_attributes=True)