import http
import logging
import uuid

from fastapi import HTTPException
from pwdlib import PasswordHash

from src.clients.report_service_client import ReportServiceClient
from src.database.batch_refresh import batch_refresh
from src.exceptions import (
    AlreadyExistsException,
    ExternalServiceUnavailableException,
    ObjectNotFoundException,
)
from src.exceptions.external_service import ExternalServiceClientException
from src.mappers.task_mapper import to_task_api_request, to_task_orm, add_report_to_task
from src.models.tasks import TaskORM
from src.models.users import UserORM
from src.database.unit_of_work import UnitOfWork
from src.repositories.user_rep import UsersRepository
from src.schemas.pagination_schema import PaginationParamsSchema
from src.schemas.tasks_schemas import (
    DeleteTasksStatsSchema,
    TaskAPIResponseSchema,
    TasksDeleteSchema,
)
from src.schemas.users_schemas import (
    BulkDeletionResponseSchema,
    ExistedUserRequestSchema,
    UserRequestSchema,
    UserResponse,
    UsersTasksPaginatedResponse,
    UserTasksDeleteSchema,
    UserTasksGetSchema,
    UserTasksShortGetSchema,
    UserUpdateWithTasksSchema,
)


class UserTaskService:

    def __init__(
        self,
        user_rep: UsersRepository,
        report_client: ReportServiceClient,
        uow: UnitOfWork,
    ) -> None:
        self.user_rep = user_rep
        self.report_client = report_client
        self.uow = uow
        self.password_hash = PasswordHash.recommended()

        self.logger = logging.getLogger(self.__class__.__name__)

    async def _create_user_and_base_tasks(
        self,
        user_data: UserRequestSchema,
    ) -> tuple[UserORM, list[TaskORM]]:
        user_orm = await self.user_rep.upsert_user(user_data)
        if user_orm is None:
            self.logger.warning(
                "Race condition detected: user with this email already exists",
                extra={"email": user_data.email},
            )
            raise AlreadyExistsException(
                detail=f"User with email {user_data.email} already exists"
            ) from None

        new_tasks_orm = [to_task_orm(t) for t in user_data.tasks]
        user_orm.tasks.extend(new_tasks_orm)
        return user_orm, new_tasks_orm

    async def _fetch_reports(
        self,
        tasks: list[TaskORM],
    ) -> dict[uuid.UUID, TaskAPIResponseSchema]:
        requests = [to_task_api_request(task) for task in tasks]
        reports = await self.report_client.get_reports_batch(requests)
        return {r.task_id: r for r in reports}

    def _enrich_tasks_with_reports(
        self,
        tasks: list[TaskORM],
        reports_by_id: dict[uuid.UUID, TaskAPIResponseSchema],
    ) -> None:
        for task in tasks:
            report = reports_by_id.get(task.id)
            if report is not None:
                add_report_to_task(task=task, report=report)
                self.logger.info(
                    "Task enriched with report",
                    extra={"task_id": str(task.id)},
                )
            else:
                self.logger.info(
                    "Report not returned for task, will be filled by worker",
                    extra={"task_id": str(task.id)},
                )

    async def create_user_with_tasks(self, user_data: UserRequestSchema) -> UserTasksGetSchema:
        check_unique_email = await self.user_rep.one_or_none(email=user_data.email)
        if check_unique_email:
            self.logger.warning(
                "User with email already exists",
                extra={"email": user_data.email},
            )
            raise AlreadyExistsException(detail=f"User with email {user_data.email} already exists")

        async with self.uow:
            user_orm, new_tasks_orm = await self._create_user_and_base_tasks(user_data)
        self.logger.info(
            "User and tasks created (status=PENDING)",
            extra={
                "user_id": str(user_orm.id),
                "tasks_count": len(new_tasks_orm),
            },
        )
        async with self.uow:
            reports_by_id = await self._fetch_reports(new_tasks_orm)
            self._enrich_tasks_with_reports(new_tasks_orm, reports_by_id)

        self.logger.info(
            "Tasks enriched with reports successfully",
            extra={"user_id": str(user_orm.id)},
        )

        return UserTasksGetSchema.model_validate(user_orm, from_attributes=True)

    def _prepare_tasks_to_add(
        self,
        user_data: ExistedUserRequestSchema,
        existing_user: UserORM,
    ) -> list[TaskORM] | None:

        existing_titles = {task.title for task in existing_user.tasks}
        new_tasks_data = [t for t in user_data.tasks if t.title not in existing_titles]
        if not new_tasks_data:
            return None
        return [to_task_orm(t) for t in new_tasks_data]

    async def add_tasks_to_user(self, user_data: ExistedUserRequestSchema) -> UserResponse:
        existing_user = await self.user_rep.get_one_or_none_with_relationship(id=user_data.id)
        if not existing_user:
            self.logger.warning(
                "User with id not found",
                extra={"id": user_data.id},
            )
            raise ObjectNotFoundException(detail=f"User with id {user_data.id} not found")

        new_tasks_to_add = self._prepare_tasks_to_add(user_data, existing_user)
        if not new_tasks_to_add:
            self.logger.info(
                "No new tasks to add",
                extra={"user_id": str(existing_user.id)},
            )
            return UserResponse(
                status="OK",
                description=f"Задачи для пользователя с ид {existing_user.id} не переданы или уже существуют",
            )
        async with self.uow:
            existing_user.tasks.extend(new_tasks_to_add)
            await batch_refresh(self.uow.session,existing_user, *new_tasks_to_add)
            try:
                reports_by_id = await self._fetch_reports(new_tasks_to_add)
                self._enrich_tasks_with_reports(new_tasks_to_add, reports_by_id)
            except (ExternalServiceUnavailableException, ExternalServiceClientException) as e:
                await self.uow.session.commit()
                self.uow._is_active = False
                self.logger.warning(
                    "Report service failed, tasks saved as PENDING, will be filled by worker",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "user_id": str(existing_user.id),
                    },
                )
                raise

            self.logger.info(
                "Tasks add to user successfully",
                extra={
                    "user_id": str(existing_user.id),
                    "tasks_count": len(new_tasks_to_add),
                },
            )
            return UserResponse(
                status="OK",
                description=f"Пользователю с ид {existing_user.id} добавлено {len(new_tasks_to_add)} задач",
            )

    async def get_user_by_id(self, user_id: uuid.UUID) -> UserTasksGetSchema:
        user = await self.user_rep.get_one_or_none_with_relationship(id=user_id)
        if not user:
            self.logger.warning("User not found", extra={"user_id": str(user_id)})
            raise ObjectNotFoundException(detail=f"User with user_id {str(user_id)} not found")

        self.logger.debug("User retrieved successfully", extra={"user_id": str(user_id)})
        return UserTasksGetSchema.model_validate(user, from_attributes=True)

    async def get_all_users(
        self, pagination: PaginationParamsSchema
    ) -> UsersTasksPaginatedResponse:
        users = await self.user_rep.get_all(
            limit=pagination.limit,
            cursor=pagination.cursor,
        )
        next_cursor = users[-1].created_at if users else None
        items = [
            UserTasksShortGetSchema.model_validate(user, from_attributes=True) for user in users
        ]
        self.logger.debug("Users retrieved", extra={"count": len(users)})
        return UsersTasksPaginatedResponse(
            items=items,
            next_cursor=next_cursor,
        )

    async def update_user_and_tasks(
        self, update_data: UserUpdateWithTasksSchema
    ) -> UserTasksGetSchema:
        async with self.uow:
            user = await self.user_rep.get_one_or_none_with_relationship(id=update_data.id)
            if not user:
                self.logger.warning("User not found", extra={"user_id": str(update_data.id)})
                raise ObjectNotFoundException(
                    detail=f"User with user_id {str(update_data.id)} not found"
                )

            user_update_dict = update_data.model_dump(
                exclude_unset=True, exclude={"id", "tasks", "password"}
            )
            for field, value in user_update_dict.items():
                setattr(user, field, value)

            if update_data.password:
                hashed_password = self.password_hash.hash(update_data.password)
                setattr(user, "hashed_password", hashed_password)

            if update_data.tasks:
                existing_tasks_map = {task.id: task for task in user.tasks}
                existing_tasks_title = {task.title for task in user.tasks}

                for task_update in update_data.tasks:
                    if task_update.title in existing_tasks_title:
                        self.logger.info(
                            "Task already exists, skipping",
                            extra={"user_id": str(user.id), "task_title": task_update.title},
                        )
                        continue

                    if task_update.id not in existing_tasks_map:
                        self.logger.warning(
                            "Task not found for user",
                            extra={"user_id": str(user.id), "task_id": str(task_update.id)},
                        )
                        raise HTTPException(
                            status_code=http.HTTPStatus.NOT_FOUND,
                            detail=f"Task with id {task_update.id} not found for this user",
                        )

                    task_orm = existing_tasks_map[task_update.id]
                    task_update_dict = task_update.model_dump(exclude_unset=True, exclude={"id"})
                    for field, value in task_update_dict.items():
                        setattr(task_orm, field, value)

            await self.uow.session.refresh(user)
        self.logger.info("User and tasks updated successfully", extra={"user_id": str(user.id)})
        return UserTasksGetSchema.model_validate(user, from_attributes=True)

    async def delete_users_tasks(
        self,
        delete_info: UserTasksDeleteSchema,
    ) -> BulkDeletionResponseSchema:
        async with self.uow:
            tasks_stats = DeleteTasksStatsSchema()
            deleted_users_count = 0

            try:
                if delete_info.delete_tasks:
                    tasks_stats = await self._delete_tasks_by_users(delete_info.delete_tasks)
                    self.logger.info(
                        "Tasks deletion completed",
                        extra={
                            "deleted_count": tasks_stats.deleted,
                            "skipped_count": tasks_stats.skipped,
                        },
                    )

                if delete_info.delete_users:
                    deleted_users_count = await self.user_rep.delete_bulk_by_ids(
                        delete_info.delete_users
                    )
                    self.logger.info("Users deleted", extra={"count": deleted_users_count})

            except Exception as e:
                self.logger.error("Bulk deletion failed", extra={"error": str(e)}, exc_info=True)
                raise HTTPException(
                    status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                    detail=f"Ошибка при удалении: {str(e)}",
                )

        self.logger.info(
            "Bulk deletion completed successfully",
        )
        return BulkDeletionResponseSchema(
            status="success",
            message="Данные успешно удалены",
            deleted_users_count=deleted_users_count,
            deleted_tasks_count=tasks_stats.deleted,
        )

    async def _delete_tasks_by_users(
        self,
        tasks_to_delete: list[TasksDeleteSchema],
    ) -> DeleteTasksStatsSchema:

        deleted_count = 0
        skipped_count = 0

        tasks_by_user = {}
        for task in tasks_to_delete:
            if task.user_id not in tasks_by_user:
                tasks_by_user[task.user_id] = []
            tasks_by_user[task.user_id].append(task.task_id)

        for user_id, task_ids in tasks_by_user.items():
            user = await self.user_rep.get_one_or_none_with_relationship(id=user_id)

            if user is None:
                self.logger.warning(
                    "User not found, skipping tasks deletion",
                    extra={
                        "user_id": str(user_id),
                        "task_ids": [str(tid) for tid in task_ids],
                    },
                )
                skipped_count += len(task_ids)
                continue

            task_by_id = {task.id: task for task in user.tasks}

            for task_id in task_ids:
                task_orm = task_by_id.get(task_id)
                if task_orm:
                    user.tasks.remove(task_orm)
                    deleted_count += 1
                else:
                    self.logger.warning(
                        "Task not found for user, skipping",
                        extra={
                            "user_id": str(user_id),
                            "task_id": str(task_id),
                        },
                    )
                    skipped_count += 1

            await self.uow.session.flush()

        return DeleteTasksStatsSchema(
            deleted=deleted_count,
            skipped=skipped_count,
        )
