from datetime import datetime
from typing import Any, TypeVar, Generic, Type

from sqlalchemy import select, ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession


Model = TypeVar("Model")
Schema = TypeVar("Schema")

class BaseRepository(Generic[Model, Schema]):
    model: Type[Model]
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_pages_with_any_parameters(
        self,
        limit: int,
        cursor: datetime | None = None,
        cursor_field: str = "created_at",
        with_lock: bool = True,
        *filters: ColumnElement[bool],
        **filter_by: Any
    ) -> list[Model]:
        cursor_column = getattr(self.model, cursor_field)
        query = (
            select(self.model)
            .filter(*filters)
            .filter_by(**filter_by)
            .with_for_update(
                read=True,
                skip_locked=True)
        )
        if cursor is not None:
            query = query.where(self.model.cursor_field < cursor)
        query = query.order_by(cursor_column.desc()).limit(limit)
        if with_lock:
            query = query.with_for_update(read=True)
        query_result = await self.session.execute(query)
        return list(query_result.scalars().unique().all())

    async def one_or_none(self, **filters: Any) -> Model | None:
        query = select(self.model).filter_by(**filters)
        query_result = await self.session.execute(query)
        result = query_result.scalars().one_or_none()
        return result

    async def save_orm_object(self, obj: Any) -> Model:
        self.session.add(obj)
        return obj

    async def add_many(self, objects: list[Model]) -> list[Model]:
        self.session.add_all(objects)
        await self.session.flush()
        return objects
