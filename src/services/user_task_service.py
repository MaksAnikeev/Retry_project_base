import logging
import uuid

import circuitbreaker
from pwdlib import PasswordHash
from sqlalchemy import text

from src.clients.report_service_client import ReportServiceClient
from src.database.unit_of_work import UnitOfWork
from src.exceptions import AlreadyExistsException, ObjectNotFoundException, ExternalServiceUnavailableException
from src.exceptions.external_service import ExternalServiceClientException
from src.mappers.task_mapper import (
    add_report_to_task,
    to_task_api_request,
    to_task_orm,
    update_task_fields,
    map_tasks_for_update,
)
from src.mappers.user_mapper import to_user_orm, update_user_fields
from src.models.tasks import TaskORM
from src.models.users import UserORM
from src.repositories.user_rep import UsersRepository
from src.schemas.pagination_schema import PaginationParamsSchema
from src.schemas.tasks_schemas import (
    TaskAPIResponseSchema
)
from src.schemas.users_schemas import (
    UserRequestSchema,
    UsersTasksPaginatedResponse,
    UserTasksGetSchema,
    UserTasksShortGetSchema,
    UserUpdateWithTasksSchema, DeletionResponseSchema,
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
        normalized_email: str
    ) -> tuple[UserORM, list[TaskORM]]:
        user_id = await self.user_rep.create_user_if_absent(to_user_orm(user_data))
        if user_id is None:
            self.logger.warning(
                "User with this email already exists",
                extra={"email": normalized_email},
            )
            raise AlreadyExistsException(
                detail=f"User with email {normalized_email} already exists"
            ) from None

        new_tasks_orm = [to_task_orm(t) for t in user_data.tasks]
        user_orm = await self.user_rep.get_one_or_none_with_relationship(id=user_id)
        user_orm.tasks = new_tasks_orm
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
        if len(tasks) != len(reports_by_id):
            self.logger.error(
                "Mismatch between requested tasks and received reports",
                extra={
                    "requested_tasks_count": len(tasks),
                    "received_reports_count": len(reports_by_id),
                    "task_ids": [str(t.id) for t in tasks],
                },
            )
            raise ExternalServiceClientException(
                detail=f"Несоответствие данных: запрошено {len(tasks)} задач, получено {len(reports_by_id)} отчетов"
            )
        for task in tasks:
            report = reports_by_id.get(task.id)
            if report is None:
                raise ExternalServiceClientException(
                    detail=f"Отчет для задачи {task.id} отсутствует в ответе сервиса"
                )
            add_report_to_task(task=task, report=report)



    async def _fetch_and_apply_reports(self, tasks: list[TaskORM], user_orm: UserORM) -> None:
        try:
            reports_by_id = await self._fetch_reports(tasks)
            self._enrich_tasks_with_reports(tasks, reports_by_id)

        except circuitbreaker.CircuitBreakerError as e:
            self.logger.error(
                "Circuit breaker is OPEN - service temporarily unavailable",
                extra={
                    "user_id": str(user_orm.id),
                    "tasks_count": len(tasks),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=False,
            )
            raise ExternalServiceUnavailableException(
                detail="Service temporarily unavailable (circuit breaker open)"
            )

        except ExternalServiceUnavailableException as e:
            self.logger.error(
                "Failed to fetch reports during user creation",
                extra={
                    "user_id": str(user_orm.id),
                    "tasks_count": len(tasks),
                    "error": str(e),
                },
            )
            raise

    async def create_user_with_tasks(self, user_data: UserRequestSchema) -> UserTasksGetSchema:
        new_email = str(user_data.email).lower().strip()
        async with self.uow:
            await self._acquire_email_lock(new_email)
            user_orm, new_tasks_orm = await self._create_user_and_base_tasks(user_data, new_email)
        self.logger.info(
            "User and tasks created (status=PENDING)",
            extra={
                "user_id": str(user_orm.id),
                "tasks_count": len(new_tasks_orm),
            },
        )
        await self._fetch_and_apply_reports(new_tasks_orm, user_orm)

        async with self.uow:
            await self.uow.session.flush()

        self.logger.info(
            "Tasks enriched with reports successfully",
            extra={"user_id": str(user_orm.id)},
        )

        return UserTasksGetSchema.model_validate(user_orm, from_attributes=True)

    async def _get_and_validate_user(self, user_id: uuid.UUID) -> UserORM:
        user = await self.user_rep.get_one_or_none_with_relationship(id=user_id)
        if not user:
            self.logger.warning("User not found", extra={"user_id": str(user_id)})
            raise ObjectNotFoundException(detail=f"User with id {user_id} not found")
        return user

    def _validate_tasks_update(
        self, update_data: UserUpdateWithTasksSchema, existing_user: UserORM
    ) -> None:
        existing_titles = {task.title for task in existing_user.tasks}
        existing_tasks_by_id = {task.id: task for task in existing_user.tasks}
        for task_data in update_data.tasks:
            if task_data.id:
                if task_data.id not in existing_tasks_by_id:
                    raise ObjectNotFoundException(
                        detail=f"Task with id {task_data.id} not found for this user"
                    )
                if task_data.title and task_data.title in existing_titles:
                    current_task = existing_tasks_by_id[task_data.id]
                    if task_data.title != current_task.title:
                        raise AlreadyExistsException(
                            detail=f"Task with title '{task_data.title}' already exists"
                        )
            else:
                if task_data.title in existing_titles:
                    raise AlreadyExistsException(
                        detail=f"Task with title '{task_data.title}' already exists"
                    )

    async def _acquire_user_lock(self, user_id: uuid.UUID) -> None:
        await self.uow.session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext('user:' || :user_id)::bigint)"),
            {"user_id": str(user_id)}
        )

    async def _acquire_email_lock(self, email: str) -> None:
        await self.uow.session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext('email:' || :email)::bigint)"),
            {"email": email.lower().strip()}
        )

    async def _validate_and_lock_email(
        self,
        update_data: UserUpdateWithTasksSchema,
        existing_user: UserORM,
    ) -> None:
        if update_data.email is not None:
            new_email = str(update_data.email).lower().strip()
            if new_email != existing_user.email:
                await self._acquire_email_lock(new_email)
                email_exists = await self.user_rep.is_email_taken(
                    email=new_email,
                    exclude_user_id=update_data.id
                )
                if email_exists:
                    self.logger.warning(
                        "Email already exists",
                        extra={
                            "user_id": str(update_data.id),
                            "conflicting_email": new_email,
                        },
                    )
                    raise AlreadyExistsException(
                        detail=f"Пользователь с email {new_email} уже существует"
                    )

    async def update_user_and_tasks(
        self, update_data: UserUpdateWithTasksSchema
    ) -> UserTasksGetSchema:
        async with self.uow:
            await self._acquire_user_lock(update_data.id)
            existing_user = await self._get_and_validate_user(update_data.id)
            await self._validate_and_lock_email(update_data, existing_user)

            self._validate_tasks_update(update_data, existing_user)
            new_tasks_orm, tasks_to_update = map_tasks_for_update(update_data)


            update_user_fields(update_data, existing_user, self.password_hash)

            if new_tasks_orm:
                existing_user.tasks.extend(new_tasks_orm)

            if tasks_to_update:
                existing_tasks_map = {task.id: task for task in existing_user.tasks}
                for task_update in tasks_to_update:
                    task_orm = existing_tasks_map[task_update.id]
                    update_task_fields(task_update, task_orm)
            await self.uow.session.flush()
            await self.uow.session.refresh(existing_user)
            response_schema = UserTasksGetSchema.model_validate(existing_user, from_attributes=True)

        self.logger.info(
            "User and tasks updated successfully",
            extra={
                "user_id": str(existing_user.id),
                "tasks_added": len(new_tasks_orm),
                "tasks_updated": len(tasks_to_update),
            },
        )
        return response_schema

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

    async def delete_user_or_tasks(
        self,
        user_id: uuid.UUID,
        task_ids: list[uuid.UUID] | None = None,
    ) -> DeletionResponseSchema:
        existing_user = await self._get_and_validate_user(user_id=user_id)
        async with self.uow:
            if not task_ids:
                existing_user.is_deleted = True
                for task in existing_user.tasks:
                    task.is_deleted = True
            else:
                requested_task_ids = set(task_ids)
                existing_task_ids = {task.id for task in existing_user.tasks}
                missing_task_ids = requested_task_ids - existing_task_ids
                if missing_task_ids:
                    missing_str = ", ".join(str(tid) for tid in sorted(missing_task_ids))
                    raise ObjectNotFoundException(
                        detail=f"Задачи с ID [{missing_str}] не найдены у пользователя {user_id}"
                    )
                for task in existing_user.tasks:
                    if task.id in requested_task_ids:
                        task.is_deleted = True
        self.logger.info(
            "Deletion completed successfully",
            extra={
                "user_id": str(user_id),
                "deleted_entities": "user_and_all_tasks" if not task_ids else "specific_tasks",
            },
        )

        return DeletionResponseSchema(
            status="success",
            message="Данные успешно удалены"
        )