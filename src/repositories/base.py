import logging
from typing import List, Sequence, Any

import sqlalchemy
from asyncpg import UniqueViolationError, ForeignKeyViolationError

from pydantic import BaseModel
from sqlalchemy import select, insert, update, inspect, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions import (
    ObjectNotFoundException,
    TooLongParameterException,
    TooManyObjectsException,
    AlreadyExistedException,
)
from src.repositories.utils import check_safe_filters


class BaseRepository:
    model: None
    mapper: None
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        self.session = session
        # Автоматически собираем все колонки модели (только один раз)
        self._allowed_filters = (
            {column.key for column in inspect(self.model).columns}
            if self.model
            else set()
        )

    def _get_safe_filters(self, filters: dict) -> dict:
        """
        Возвращает только те фильтры, которые реально существуют в модели.
        Защита от инъекций и опечаток.
        """
        if not self._allowed_filters:
            raise ValueError("Модель не задана или не имеет колонок")

        return {k: v for k, v in filters.items() if k in self._allowed_filters}

    def _to_schemas(self, items) -> List[BaseModel]:
        """
        Валидируем возвращаемый список объектов под пайдентик схему, заданную в атрибутах schema
        """
        if self.mapper is None:
            raise NotImplementedError("schema не задан в наследнике")
        return [self.mapper.map_to_domain_entity(item) for item in items]

    async def _check_quantity_obj(self, safe_filters) -> BaseModel:
        """
        Проверяет количество объектов фильтрации перед изменением или удалением
        """
        query = select(self.model).filter_by(**safe_filters)
        try:
            query_result = await self.session.execute(query)
        except sqlalchemy.exc.DBAPIError:
            raise TooLongParameterException

        existing = query_result.scalars().all()
        if not existing:
            raise ObjectNotFoundException
        if len(existing) > 1:
            raise TooManyObjectsException
        return self.mapper.map_to_domain_entity(existing[0])

    async def get_all_with_parameters(self, **filter_by) -> list[BaseModel | Any]:
        safe_filters = self._get_safe_filters(filter_by)
        check_safe_filters(safe_filters)
        query = select(self.model).filter_by(**safe_filters)
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

    async def get_one(self, **filters) -> BaseModel | None | Any:
        safe_filters = self._get_safe_filters(filters)
        check_safe_filters(safe_filters)
        existing = await self._check_quantity_obj(safe_filters)
        return existing

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
        return self.mapper.map_to_domain_entity(result.scalars().one())

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
        safe_filters = self._get_safe_filters(filters)
        check_safe_filters(safe_filters)
        existing = await self._check_quantity_obj(safe_filters)
        stmt = (
            update(self.model)
            .where(self.model.id == existing.id)
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
        return self.mapper.map_to_domain_entity(new_result.scalars().one())

    async def delete(self, **filters) -> BaseModel:
        safe_filters = self._get_safe_filters(filters)
        check_safe_filters(safe_filters)
        existing = await self._check_quantity_obj(safe_filters)
        stmt = (
            delete(self.model).where(self.model.id == existing.id).returning(self.model)
        )

        delete_result = await self.session.execute(stmt)
        return self.mapper.map_to_domain_entity(delete_result.scalars().one())

    async def delete_bulk(
        self,
        attribute: str | None = None,
        ids_for_delete: list | None = None,
        **filters,
    ):
        safe_filters = self._get_safe_filters(filters)
        check_safe_filters(safe_filters)
        query_for_delete = select(self.model.id).filter_by(**safe_filters)
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
