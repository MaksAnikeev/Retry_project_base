import logging
import uuid

from pwdlib import PasswordHash

from src.clients.report_service_client import ReportServiceClient
from src.database.unit_of_work import UnitOfWork
from src.exceptions import AlreadyExistsException, ObjectNotFoundException
from src.mappers.task_mapper import (
    add_report_to_task,
    to_task_api_request,
    to_task_orm,
    update_task_fields,
)
from src.mappers.user_mapper import to_user_orm, update_user_fields
from src.models.tasks import TaskORM
from src.models.users import UserORM
from src.repositories.user_rep import UsersRepository
from src.schemas.pagination_schema import PaginationParamsSchema
from src.schemas.tasks_schemas import (
    TaskAPIResponseSchema,
    TaskRequestSchema,
    TasksDeleteSchema,
    TaskUpdateSchema,
)
from src.schemas.users_schemas import (
    BulkDeletionResponseSchema,
    UserRequestSchema,
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
        user_id = await self.user_rep.create_user_if_absent(to_user_orm(user_data))
        if user_id is None:
            self.logger.warning(
                "User with this email already exists",
                extra={"email": user_data.email},
            )
            raise AlreadyExistsException(
                detail=f"User with email {user_data.email} already exists"
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
        enriched_count = 0
        skipped_count = 0
        for task in tasks:
            report = reports_by_id.get(task.id)
            if report is not None:
                add_report_to_task(task=task, report=report)
                self.logger.debug(
                    "Task enriched with report",
                    extra={"task_id": str(task.id)},
                )
                enriched_count += 1
            else:
                self.logger.debug(
                    "Report not returned for task, will be filled by worker",
                    extra={"task_id": str(task.id)},
                )
                skipped_count += 1
        self.logger.info(
            "Batch tasks enrichment completed",
            extra={
                "total_tasks": len(tasks),
                "enriched_count": enriched_count,
                "skipped_count": skipped_count,
            },
        )

    async def _fetch_and_apply_reports(self, tasks: list[TaskORM]) -> None:
        reports_by_id = await self._fetch_reports(tasks)
        self._enrich_tasks_with_reports(tasks, reports_by_id)

    async def create_user_with_tasks(self, user_data: UserRequestSchema) -> UserTasksGetSchema:
        async with self.uow:
            user_orm, new_tasks_orm = await self._create_user_and_base_tasks(user_data)
        self.logger.info(
            "User and tasks created (status=PENDING)",
            extra={
                "user_id": str(user_orm.id),
                "tasks_count": len(new_tasks_orm),
            },
        )
        await self._fetch_and_apply_reports(new_tasks_orm)

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
        existing_ids = {task.id for task in existing_user.tasks}
        for task_data in update_data.tasks:
            if task_data.id:
                if task_data.id not in existing_ids:
                    raise ObjectNotFoundException(
                        detail=f"Task with id {task_data.id} not found for this user"
                    )
                if task_data.title and task_data.title in existing_titles:
                    current_task = next(t for t in existing_user.tasks if t.id == task_data.id)
                    if task_data.title != current_task.title:  # Тайтл действительно меняется
                        raise AlreadyExistsException(
                            detail=f"Task with title '{task_data.title}' already exists"
                        )
            else:
                if task_data.title in existing_titles:
                    raise AlreadyExistsException(
                        detail=f"Task with title '{task_data.title}' already exists"
                    )

    def _map_tasks_for_update(
        self, update_data: UserUpdateWithTasksSchema
    ) -> tuple[list[TaskORM], list[TaskUpdateSchema]]:

        tasks_to_add_orm = []
        tasks_to_update = []
        for task_data in update_data.tasks:
            if task_data.id:
                tasks_to_update.append(task_data)
            else:
                valid_task = TaskRequestSchema.model_validate(task_data.model_dump())
                tasks_to_add_orm.append(to_task_orm(valid_task))
        return tasks_to_add_orm, tasks_to_update

    async def update_user_and_tasks(
        self, update_data: UserUpdateWithTasksSchema
    ) -> UserTasksGetSchema:
        existing_user = await self._get_and_validate_user(update_data.id)
        self._validate_tasks_update(update_data, existing_user)
        new_tasks_orm, tasks_to_update = self._map_tasks_for_update(update_data)

        async with self.uow:
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

    async def delete_users_tasks(
        self,
        delete_info: UserTasksDeleteSchema,
    ) -> BulkDeletionResponseSchema:
        async with self.uow:
            deleted_tasks_count = 0
            if delete_info.delete_tasks:
                await self._delete_tasks_by_users(delete_info.delete_tasks)
                deleted_tasks_count = len(set(delete_info.delete_tasks.task_ids))

            deleted_users_count = 0
            if delete_info.delete_users:
                deleted_users_count = await self.user_rep.delete_bulk_by_ids(
                    delete_info.delete_users
                )
                if deleted_users_count != len(set(delete_info.delete_users)):
                    raise ObjectNotFoundException(
                        detail="Один или несколько пользователей не найдены"
                    )

        self.logger.info(
            "Bulk deletion completed successfully",
            extra={
                "deleted_tasks_count": deleted_tasks_count,
                "deleted_users_count": deleted_users_count,
            },
        )
        return BulkDeletionResponseSchema(
            status="success",
            message="Данные успешно удалены",
            deleted_users_count=deleted_users_count,
            deleted_tasks_count=deleted_tasks_count,
        )

    async def _delete_tasks_by_users(
        self,
        tasks_to_delete: TasksDeleteSchema,
    ) -> None:

        existing_user = await self._get_and_validate_user(user_id=tasks_to_delete.user_id)
        existing_task_ids = {task.id for task in existing_user.tasks}
        tasks_to_delete_ids = set(tasks_to_delete.task_ids)

        if not tasks_to_delete_ids.issubset(existing_task_ids):
            raise ObjectNotFoundException(
                detail=f"Одна или несколько задач не найдены у пользователя {existing_user.id}"
            )

        for task in existing_user.tasks:
            if task.id in tasks_to_delete_ids:
                task.is_deleted = True
