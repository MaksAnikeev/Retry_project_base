import logging
from typing import List, Sequence, Any

from asyncpg import UniqueViolationError, ForeignKeyViolationError

from pydantic import BaseModel
from sqlalchemy import select, insert, update, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions.exceptions import (
    ObjectNotFoundException,
    AlreadyExistedException,
)


class BaseRepository:
    model: None
    schemas: None
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_schemas(self, items) -> List[BaseModel]:
        """
        Валидируем возвращаемый список объектов под пайдентик схему, заданную в атрибутах schema
        """
        if self.schemas is None:
            raise NotImplementedError("schema не задан в наследнике")
        return [self.schemas.model_validate(item, from_attributes=True) for item in items]


    async def get_all_with_parameters(self, **filter_by) -> list[BaseModel | Any]:
        query = select(self.model).filter_by(**filter_by)
        query_result = await self.session.execute(query)
        result = query_result.scalars().all()
        return self._to_schemas(result)

    async def get_all_with_any_parameters(
        self, *filter, **filter_by
    ) -> list[BaseModel | Any]:
        query = select(self.model).filter(*filter).filter_by(**filter_by)
        query_result = await self.session.execute(query)
        result = query_result.scalars().all()
        return self._to_schemas(result)

    async def get_all(self, *args, **kwargs) -> list[BaseModel | Any]:
        query = select(self.model)
        query_result = await self.session.execute(query)
        result = query_result.scalars().all()
        return self._to_schemas(result)

    async def one_or_none(self, **filters) -> BaseModel | None | Any:
        query = select(self.model).filter_by(**filters)
        query_result = await self.session.execute(query)
        result = query_result.scalars().one_or_none()
        return result

    async def add(self, data: BaseModel) -> BaseModel | Any:
        stmt = insert(self.model).values(**data.model_dump()).returning(self.model)
        # print(stmt.compile(async_engine, compile_kwargs={'literal_binds': True}))
        try:
            result = await self.session.execute(stmt)
        except IntegrityError as ex:
            if isinstance(ex.orig.__cause__, UniqueViolationError):
                logging.error(
                    f"Ошибка при попытки создать объект с уже существующими уникальными параметрами /"
                    f"Входные данные {data.model_dump()}"
                )
                raise AlreadyExistedException
            elif isinstance(ex.orig.__cause__, ForeignKeyViolationError):
                logging.error(
                    f"Ошибка при попытки создать объект с несуществующим значением ForeignKey /"
                    f"Входные данные {data.model_dump()}"
                )
                raise ObjectNotFoundException
            else:
                logging.error(
                    f"Неизвестная ошибка: {ex}. Входные данные {data.model_dump()}"
                )
                raise ex
        logging.info(f"Объект успешно создан. Данные {data.model_dump()}")
        return self.schemas.model_validate(result.scalars().one(), from_attributes=True)

    async def add_bulk(self, data: Sequence[BaseModel]):
        stmt = insert(self.model).values([item.model_dump() for item in data])
        try:
            await self.session.execute(stmt)
        except IntegrityError as ex:
            if isinstance(ex.orig.__cause__, ForeignKeyViolationError):
                raise ObjectNotFoundException
            else:
                raise ex

    async def edit(self, data: BaseModel, **filters) -> BaseModel:
        query = select(self.model).filter_by(**filters)
        query_result = await self.session.execute(query)
        result = query_result.scalars().one_or_none()
        if not result:
            raise ObjectNotFoundException

        stmt = (
            update(self.model)
            .where(self.model.id == result.id)
            .values(**data.model_dump(exclude_unset=True))
            .returning(self.model)
        )
        try:
            new_result = await self.session.execute(stmt)
        except IntegrityError as ex:
            if isinstance(ex.orig.__cause__, ForeignKeyViolationError):
                raise ObjectNotFoundException
            else:
                raise ex
        return self.schemas.model_validate(new_result.scalars().one(), from_attributes=True)

    async def delete(self, **filters) -> BaseModel:
        query = select(self.model).filter_by(**filters)
        query_result = await self.session.execute(query)
        result = query_result.scalars().one_or_none()
        if not result:
            raise ObjectNotFoundException
        stmt = (
            delete(self.model).where(self.model.id == result.id).returning(self.model)
        )
        delete_result = await self.session.execute(stmt)
        return self.schemas.model_validate(delete_result.scalars().one(), from_attributes=True)

    async def delete_bulk(
        self,
        attribute: str | None = None,
        ids_for_delete: list | None = None,
        **filters,
    ):
        query_for_delete = select(self.model.id).filter_by(**filters)
        if attribute and ids_for_delete and hasattr(self.model, attribute):
            query_for_delete = query_for_delete.where(
                getattr(self.model, attribute).in_(ids_for_delete)
            )

        stmt = delete(self.model).where(self.model.id.in_(query_for_delete))
        delete_result = await self.session.execute(stmt)
        deleted_objects = delete_result.scalars().all()
        await self.session.commit()
        return self._to_schemas(deleted_objects)

    async def delete_all(self):
        stmt = delete(self.model).returning(self.model)
        delete_result = await self.session.execute(stmt)
        deleted_objects = delete_result.scalars().all()
        return self._to_schemas(deleted_objects)

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
