import logging
import uuid

from fastapi import HTTPException
from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError

from src.clients.report_http_client import ReportServiceClient
from src.exceptions import UserNotFoundException, ExternalServiceUnavailableException, BaseDomainException
from src.exceptions.infra import ExternalServiceClientException
from src.exceptions.integrity import DatabaseConstraintException
from src.models.tasks import TaskORM
from src.models.users import UserORM
from src.repositories.user_rep import UsersRepository
from src.schemas.base_schema import PaginationParamsSchema
from src.schemas.default_report_schemas import ReportLike, DefaultReport
from src.schemas.tasks_schemas import TaskAPIRequestSchema, TaskAPIResponseSchema, TasksDeleteSchema, \
    DeleteTasksStatsSchema
from src.schemas.users_schemas import (
    BulkDeletionResponseSchema,
    UserTasksDeleteSchema,
    UserTasksGetSchema,
    UserTasksShortGetSchema,
    UserUpdateWithTasksSchema, UserResponse, UserRequestSchema, UsersTasksPaginatedResponse
)


class UserTaskService:

    def __init__(
        self,
        user_rep: UsersRepository,
        http_client: ReportServiceClient,
    ) -> None:
        self.user_rep = user_rep
        self.http_client = http_client
        self.password_hash = PasswordHash.recommended()

        self.logger = logging.getLogger(self.__class__.__name__)

    def _create_task_orm(
        self,
        req: TaskAPIRequestSchema,
        report: ReportLike,
        user_id: uuid.UUID,
        is_report_pending: bool = False,
    ) -> TaskORM:
        return TaskORM(
            id=req.task_id,
            user_id=user_id,
            title=req.title,
            description=req.description,
            done=False,
            finish_date=req.finish_date,
            complexity=report.complexity,
            estimated_hours=report.estimated_hours,
            priority=report.priority,
            is_report_pending=is_report_pending,
        )

    def _prepare_task_requests(
        self,
        user_data: UserRequestSchema,
        existing_user: UserORM | None,
        user_id: uuid.UUID,
    ) -> list[TaskAPIRequestSchema] | None:

        existing_titles = (
            {task.title for task in existing_user.tasks}
            if existing_user else set()
        )
        new_tasks_data = [t for t in user_data.tasks if t.title not in existing_titles]

        if not new_tasks_data:
            return None

        return [
            TaskAPIRequestSchema(
                task_id=uuid.uuid4(),
                user_id=user_id,
                title=t.title,
                description=t.description,
                finish_date=t.finish_date,
            )
            for t in new_tasks_data
        ]

    async def _fetch_reports_safely(
        self,
        task_api_requests: list[TaskAPIRequestSchema],
        user_id: uuid.UUID,
    ) -> dict[uuid.UUID, TaskAPIResponseSchema]:
        try:
            reports = await self.http_client.get_reports_batch(task_api_requests)
            return {r.task_id: r for r in reports}

        except ExternalServiceUnavailableException as e:
            self.logger.warning(
                "Report service unavailable, will use defaults",
                extra={"user_id": str(user_id), "error": str(e)},
            )
            return {}

        except ExternalServiceClientException as e:
            self.logger.error(
                "Report service rejected request, will use defaults",
                extra={"user_id": str(user_id), "error": str(e)},
            )
            return {}

    def _build_tasks_orm(
        self,
        task_api_requests: list[TaskAPIRequestSchema],
        reports_by_id: dict[uuid.UUID, TaskAPIResponseSchema],
        user_id: uuid.UUID,
    ) -> list[TaskORM]:
        new_tasks_orm = []

        for req in task_api_requests:
            report = reports_by_id.get(req.task_id)
            is_pending = report is None

            if is_pending:
                self.logger.warning(
                    "Report not returned for task, using default",
                    extra={"task_id": str(req.task_id)},
                )
                report_like: ReportLike = DefaultReport()
            else:
                report_like = report

            new_tasks_orm.append(
                self._create_task_orm(
                    req=req,
                    report=report_like,
                    user_id=user_id,
                    is_report_pending=is_pending,
                )
            )

        return new_tasks_orm

    async def _save_user_with_tasks(
        self,
        existing_user: UserORM | None,
        new_tasks_orm: list[TaskORM],
        user_data: UserRequestSchema,
        user_id: uuid.UUID,
    ) -> UserORM:
        if existing_user:
            existing_user.tasks.extend(new_tasks_orm)
            user_to_save = existing_user
        else:
            user_to_save = UserORM(
                id=user_id,
                username=user_data.username,
                email=user_data.email,
                hashed_password=self.password_hash.hash(user_data.password),
                is_active=True,
                is_deleted=False,
            )
            user_to_save.tasks = new_tasks_orm

        try:
            saved_user = await self.user_rep.save_orm_object(user_to_save)
            await self.user_rep.commit()
            return saved_user

        except IntegrityError as e:
            await self.user_rep.rollback()
            constraint = getattr(e.orig, "constraint_name", "unknown")
            self.logger.error(
                "Database constraint violation",
                extra={"user_id": str(user_id), "constraint": constraint, "error": str(e)},
            )
            raise DatabaseConstraintException(detail=f"Constraint: {constraint}") from e

        except Exception as e:
            await self.user_rep.rollback()
            self.logger.error(
                "Save failed",
                extra={"user_id": str(user_id), "error": str(e)},
                exc_info=True,
            )
            raise BaseDomainException() from e

    async def create_user_with_tasks(self, user_data: UserRequestSchema) -> UserResponse:
        self.logger.info("Starting create_user_with_tasks", extra={"email": user_data.email})
        existing_user = await self.user_rep.get_one_or_none_with_relationship(email=user_data.email)
        user_id = existing_user.id if existing_user else uuid.uuid4()

        task_api_requests = self._prepare_task_requests(user_data, existing_user, user_id)
        if task_api_requests is None:
            if existing_user:
                self.logger.info(
                    "No new tasks to add",
                    extra={"user_id": str(existing_user.id)},
                )
                return UserResponse(
                    status="OK",
                    description=f"Задачи для пользователя с ид {existing_user.id} не переданы или уже существуют",
                )
            else:
                self.logger.info(
                    "New user without tasks, creating empty user",
                    extra={"email": user_data.email},
                )
                task_api_requests = []

        reports_by_id = await self._fetch_reports_safely(task_api_requests, user_id)

        new_tasks_orm = self._build_tasks_orm(task_api_requests, reports_by_id, user_id)

        saved_user = await self._save_user_with_tasks(
            existing_user=existing_user,
            new_tasks_orm=new_tasks_orm,
            user_data=user_data,
            user_id=user_id,
        )

        self.logger.info(
            "User and tasks saved successfully",
            extra={
                "user_id": str(saved_user.id),
                "tasks_count": len(new_tasks_orm),
                "is_new_user": not existing_user,
            },
        )

        return UserResponse(
            status="OK",
            description=f"Задачи ({len(new_tasks_orm)} шт) для пользователя с ид {saved_user.id} успешно добавлены",
        )


    async def get_user_by_id(self, user_id: uuid.UUID) -> UserTasksGetSchema:
        self.logger.debug("Getting user by id", extra={"user_id": str(user_id)})
        user = await self.user_rep.get_one_or_none_with_relationship(id=user_id)
        if not user:
            self.logger.warning("User not found", extra={"user_id": str(user_id)})
            raise UserNotFoundException(detail = f"User with user_id {str(user_id)} not found")

        self.logger.debug("User retrieved successfully", extra={"user_id": str(user_id)})
        return UserTasksGetSchema.model_validate(user, from_attributes=True)

    async def get_all_users(
        self,
        pagination: PaginationParamsSchema
    ) -> UsersTasksPaginatedResponse:
        self.logger.debug(
            "Getting all users",
            extra={"limit": pagination.limit, "cursor": pagination.cursor}
        )
        users = await self.user_rep.get_all(
            limit=pagination.limit,
            cursor=pagination.cursor,
        )
        next_cursor = users[-1].created_at if users else None
        items = [
            UserTasksShortGetSchema.model_validate(user, from_attributes=True)
            for user in users
        ]
        self.logger.debug("Users retrieved", extra={"count": len(users)})
        return UsersTasksPaginatedResponse(
            items=items,
            next_cursor=next_cursor,
        )

    async def update_user_and_tasks(
        self, update_data: UserUpdateWithTasksSchema
    ) -> UserTasksGetSchema:
        self.logger.debug(
            "Starting update_user_and_tasks",
            extra={"user_id": update_data.id, "tasks": len(update_data.tasks)},
        )
        user = await self.user_rep.get_one_or_none_with_relationship(id=update_data.id)
        if not user:
            self.logger.warning("User not found", extra={"user_id": str(update_data.id)})
            raise UserNotFoundException(detail=f"User with user_id {str(update_data.id)} not found")

        user_update_dict = update_data.model_dump(exclude_unset=True, exclude={"id", "tasks", "password"})
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
                        extra={"user_id": str(user.id), "task_title": task_update.title}
                    )
                    continue

                if task_update.id not in existing_tasks_map:
                    self.logger.warning(
                        "Task not found for user",
                        extra={"user_id": str(user.id), "task_id": str(task_update.id)}
                    )
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
        self.logger.info("User and tasks updated successfully", extra={"user_id": str(user.id)})
        return UserTasksGetSchema.model_validate(user, from_attributes=True)

    async def delete_users_tasks(
        self,
        delete_info: UserTasksDeleteSchema,
    ) -> BulkDeletionResponseSchema:
        self.logger.info(
            "Starting bulk deletion",
            extra={
                "users_count": len(delete_info.delete_users) if delete_info.delete_users else 0,
                "tasks_count": len(delete_info.delete_tasks) if delete_info.delete_tasks else 0
            }
        )
        tasks_stats=DeleteTasksStatsSchema()
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
            await self.user_rep.commit()

            self.logger.info(
                "Bulk deletion completed successfully",
            )

            return BulkDeletionResponseSchema(
                status="success",
                message="Данные успешно удалены",
                deleted_users_count=deleted_users_count,
                deleted_tasks_count=tasks_stats.deleted,
            )
        except Exception as e:
            await self.user_rep.rollback()
            self.logger.error(
                "Bulk deletion failed",
                extra={"error": str(e)},
                exc_info=True
            )
            raise HTTPException(status_code=500, detail=f"Ошибка при удалении: {str(e)}")

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

            await self.user_rep.commit()

        return DeleteTasksStatsSchema(
            deleted=deleted_count,
            skipped=skipped_count,
        )