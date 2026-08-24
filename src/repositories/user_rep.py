from datetime import datetime
import uuid
from typing import Any

from sqlalchemy import select, inspect, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import selectinload

from src.models import UserORM
from src.repositories.base import BaseRepository
from src.schemas.users_schemas import UserGetSchema, UserRequestSchema


class UsersRepository(BaseRepository[UserORM, UserGetSchema]):
    model = UserORM

    async def get_one_or_none_with_relationship(self, **filters: Any) -> UserORM | None:
        query = select(self.model).filter_by(**filters).options(selectinload(self.model.tasks))
        query_result = await self.session.execute(query)
        return query_result.scalars().one_or_none()

    async def is_email_taken(self, email: str, exclude_user_id: uuid.UUID) -> bool:
        stmt = (
            select(self.model.id)
            .where(
                self.model.email == email,
                self.model.id != exclude_user_id
        ))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None


    async def get_existed_tasks(self, user_data: UserRequestSchema) -> UserORM | None:
        query = select(self.model).filter_by(email=user_data.email).options(selectinload(self.model.tasks))
        query_result = await self.session.execute(query)
        return query_result.scalars().one_or_none()

    async def get_all(
        self,
        limit: int,
        cursor: datetime | None = None,
    ) -> list[UserORM]:
        query = (
            select(self.model)
            .options(selectinload(self.model.tasks))
            .with_for_update(
                read=True,
                skip_locked=True)
        )

        if cursor is not None:
            query = query.where(self.model.created_at < cursor)

        query = (
            query
            .order_by(self.model.created_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(query)
        return list(result.scalars().unique().all())

    async def create_user_if_absent(self, user_orm: UserORM) -> uuid.UUID | None:
        mapper = inspect(UserORM)
        insert_data = {
            column.key: getattr(user_orm, column.key)
            for column in mapper.columns
            if column.server_default is None
        }
        stmt = insert(UserORM).values(**insert_data)
        stmt = stmt.on_conflict_do_nothing(index_elements=["email"])
        stmt = stmt.returning(UserORM.id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def acquire_user_lock(self, user_id: uuid.UUID) -> None:
        await self.session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext('user:' || :user_id)::bigint)"),
            {"user_id": str(user_id)}
        )

    async def acquire_email_lock(self, email: str) -> None:
        await self.session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext('email:' || :email)::bigint)"),
            {"email": email.lower().strip()}
        )

    async def save_and_refresh(self, user_orm: UserORM) -> UserORM:
        await self.session.flush()
        await self.session.refresh(
            user_orm,
            attribute_names=["updated_at", "created_at"],
        )
        for task in user_orm.tasks:
            await self.session.refresh(
                task,
                attribute_names=["updated_at", "created_at", "id"],
            )
        return user_orm
