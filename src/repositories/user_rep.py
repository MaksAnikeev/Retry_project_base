import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from src.models import UserORM
from src.repositories.base import BaseRepository
from src.schemas.users_schemas import UserGetSchema


class UsersRepository(BaseRepository[UserORM, UserGetSchema]):
    model = UserORM

    async def get_one_or_none_with_relationship(self, **filters: Any) -> UserORM | None:
        query = select(self.model).filter_by(**filters).options(selectinload(self.model.tasks))
        query_result = await self.session.execute(query)
        return query_result.scalars().one_or_none()

    async def get_all(
        self,
        limit: int,
        offset: int
    ) -> list[UserORM]:
        query = (
            select(self.model)
            .options(selectinload(self.model.tasks))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return list(result.scalars().unique().all())

    async def delete_bulk_by_ids(self, user_ids: list[uuid.UUID]) -> int:
        if not user_ids:
            return 0

        stmt = (
            update(self.model)
            .where(self.model.id.in_(user_ids))
            .values(is_deleted=True)
        )
        result = await self.session.execute(stmt)
        return result.rowcount
