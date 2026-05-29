from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.exceptions.exceptions import ObjectNotFoundException
from src.models import TasksORM
from src.repositories.base import BaseRepository
from src.schemas.tasks_schemas import TaskUserGetSchemas, TaskGetSchemas


class TasksRepository(BaseRepository):
    model = TasksORM
    schemas = TaskGetSchemas

    async def get_one_or_none_with_relship(self, **filters) -> BaseModel:
        query = select(self.model).filter_by(**filters)
        query_result = await self.session.execute(query)
        result = query_result.scalars().one_or_none()
        if not result:
            raise ObjectNotFoundException
        query = (
            select(self.model)
            .filter_by(**filters)
            .options(selectinload(self.model.user))  # type: ignore
        )
        query_result = await self.session.execute(query)
        result = query_result.scalars().one_or_none()
        return TaskUserGetSchemas.model_validate(result, from_attributes=True)