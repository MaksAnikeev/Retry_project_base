import logging
from typing import Any, TypeVar, Generic, Type

from sqlalchemy import select, ColumnElement
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


Model = TypeVar("Model")
Schema = TypeVar("Schema")

class BaseRepository(Generic[Model, Schema]):
    model: Type[Model]
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_with_any_parameters(
        self,
        *filters: ColumnElement[bool],
        **filter_by: Any
    ) -> list[Model]:
        query = select(self.model).filter(*filters).filter_by(**filter_by)
        query_result = await self.session.execute(query)
        return list(query_result.scalars().all())

    async def one_or_none(self, **filters: Any) -> Model | None:
        query = select(self.model).filter_by(**filters)
        query_result = await self.session.execute(query)
        result = query_result.scalars().one_or_none()
        return result


    async def save_orm_object(self, obj: Any) -> Model:
        try:
            self.session.add(obj)
            await self.session.flush()
            await self.session.refresh(obj)
            return obj
        except IntegrityError as ex:
            logging.error(f"Database integrity error on save: {ex.orig}")
            await self.session.rollback()
            raise


    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
