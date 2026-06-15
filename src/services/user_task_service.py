import logging
import uuid

from fastapi import HTTPException
from pwdlib import PasswordHash
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError

from src.clients.report_http_client import ReportServiceClient
from src.exceptions import ObjectNotFoundException
from src.models.tasks import TaskORM
from src.models.users import UserORM
from src.repositories.task_rep import TasksRepository
from src.repositories.user_rep import UsersRepository
from src.schemas.base_schema import PaginationParamsSchema
from src.schemas.tasks_schemas import TaskAPIRequestSchema, TaskUserGetSchema
from src.schemas.users_schemas import (
    BulkDeletionResponseSchema,
    UserTasksDeleteSchema,
    UserTasksGetSchema,
    UserTasksShortGetSchema,
    UserUpdateWithTasksSchema, UserResponse, UserRequestSchema
)


class UserTaskService:

    def __init__(
        self,
        user_rep: UsersRepository,
        task_rep: TasksRepository,
        http_client: ReportServiceClient,
    ) -> None:
        self.user_rep = user_rep
        self.task_rep = task_rep
        self.http_client = http_client
        self.password_hash = PasswordHash.recommended()

    async def _check_user_exists(self, user_id: uuid.UUID) -> None:
        user = await self.user_rep.one_or_none(id=user_id)
        if not user:
            logging.warning(f"User with id {user_id} not found")
            raise ObjectNotFoundException

    async def _check_task_exists(self, task_id: uuid.UUID) -> None:
        task = await self.task_rep.one_or_none(id=task_id)
        if not task:
            logging.warning(f"Task with id {task_id} not found")
            raise ObjectNotFoundException

    async def upsert_user_with_tasks(self, user_data: UserRequestSchema) -> UserResponse:
        existing_user = await self.user_rep.get_one_or_none_with_relationship(email=user_data.email)
        user_id = existing_user.id if existing_user else uuid.uuid4()

        new_tasks_orm = []

        for task_data in user_data.tasks:
            task_exists = await self.task_rep.one_or_none(user_id=user_id, title=task_data.title)
            if task_exists:
                logging.warning(
                    f"Task '{task_data.title}' already exists for user {user_id}. Skipping."
                )
                continue

            task_id = uuid.uuid4()

            task_api_info = TaskAPIRequestSchema(
                task_id=task_id,
                user_id=user_id,
                title=task_data.title,
                description=task_data.description,
                finish_date=task_data.finish_date,
            )
            report = await self.http_client.get_report(task_api_info)

            new_task = TaskORM(
                id=task_id,
                user_id=user_id,
                title=task_data.title,
                description=task_data.description,
                done=False,
                finish_date=task_data.finish_date,
                complexity=report.complexity,
                estimated_hours=report.estimated_hours,
                priority=report.priority,
            )
            new_tasks_orm.append(new_task)

        if not new_tasks_orm:
            if existing_user:
                return UserResponse(
                    status="OK",
                    description=f"Задачи для пользователя с ид {existing_user.id} не переданы или уже существуют",
                )

        if existing_user:
            existing_user.tasks.extend(new_tasks_orm)
            user_to_save = existing_user
        else:
            new_user = UserORM(
                id=user_id,
                username=user_data.username,
                email=user_data.email,
                hashed_password=self.password_hash.hash(user_data.password),
                is_active=True,
                is_deleted=False,
            )
            new_user.tasks = new_tasks_orm
            user_to_save = new_user

        try:
            saved_user = await self.user_rep.save_orm_object(user_to_save)
            await self.user_rep.commit()
            return UserResponse(
                status="OK",
                description=f"Задачи для пользователя с ид {saved_user.id} успешно добавлены",
            )
        except IntegrityError:
            raise HTTPException(status_code=409, detail="Database constraint violation")
        except Exception as e:
            await self.user_rep.rollback()
            logging.error(f"Upsert failed: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def get_user_by_id(self, user_id: uuid.UUID) -> UserTasksGetSchema:
        await self._check_user_exists(user_id=user_id)
        user = await self.user_rep.get_one_or_none_with_relationship(id=user_id)
        return UserTasksGetSchema.model_validate(user, from_attributes=True)

    async def get_task_by_id(self, task_id: uuid.UUID) -> TaskUserGetSchema:
        await self._check_task_exists(task_id=task_id)
        task = await self.task_rep.get_one_or_none_with_relationship(id=task_id)
        return TaskUserGetSchema.model_validate(task, from_attributes=True)

    async def get_all_users(self, pagination: PaginationParamsSchema) -> list[UserTasksShortGetSchema]:
        users = await self.user_rep.get_all(
            limit=pagination.per_page,
            offset=(pagination.page - 1) * pagination.per_page,
        )
        return [
            UserTasksShortGetSchema.model_validate(user, from_attributes=True) for user in users
        ]

    async def update_user_and_tasks(
        self, update_data: UserUpdateWithTasksSchema
    ) -> UserTasksGetSchema:
        await self._check_user_exists(user_id=update_data.id)
        user = await self.user_rep.get_one_or_none_with_relationship(id=update_data.id)

        user_update_dict = update_data.model_dump(exclude_unset=True, exclude={"id", "tasks", "password"})
        for field, value in user_update_dict.items():
            setattr(user, field, value)

        if update_data.password:
            hashed_password = self.password_hash.hash(update_data.password)
            setattr(user, "hashed_password", hashed_password)

        if update_data.tasks:
            existing_tasks_map = {task.id: task for task in user.tasks}

            for task_update in update_data.tasks:
                task_exists = await self.task_rep.one_or_none(user_id=user.id, title=task_update.title)
                if task_exists:
                    logging.warning(
                        f"Task '{task_update.title}' already exists for user {user.id}. Skipping."
                    )
                    continue

                if task_update.id not in existing_tasks_map:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Task with id {task_update.id} not found for this user",
                    )

                task_orm = existing_tasks_map[task_update.id]
                task_update_dict = task_update.model_dump(exclude_unset=True, exclude={"id"})
                for field, value in task_update_dict.items():
                    setattr(task_orm, field, value)

        await self.user_rep.commit()
        await self.user_rep.session.refresh(user)
        return UserTasksGetSchema.model_validate(user, from_attributes=True)

    async def delete_users_tasks(
        self,
        delete_info: UserTasksDeleteSchema,
    ) -> BulkDeletionResponseSchema:
        deleted_tasks_count = 0
        deleted_users_count = 0
        try:
            if delete_info.delete_tasks:
                conditions = [
                    and_(TaskORM.id == task.task_id, TaskORM.user_id == task.user_id)
                    for task in delete_info.delete_tasks
                ]

                deleted_tasks_count = await self.task_rep.delete_bulk_by_conditions(conditions)

            if delete_info.delete_users:
                deleted_users_count = await self.user_rep.delete_bulk_by_ids(
                    delete_info.delete_users
                )

            await self.user_rep.commit()

            return BulkDeletionResponseSchema(
                status="success",
                message="Данные успешно удалены",
                deleted_users_count=deleted_users_count,
                deleted_tasks_count=deleted_tasks_count,
            )

        except Exception as e:
            await self.user_rep.rollback()
            raise HTTPException(status_code=500, detail=f"Ошибка при удалении: {str(e)}")
