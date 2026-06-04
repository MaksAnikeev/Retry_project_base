import logging
import uuid

from sqlalchemy.exc import IntegrityError
from asyncpg import UniqueViolationError, ForeignKeyViolationError

from src.clients.report_http_client import ReportServiceClient
from src.exceptions import ObjectNotFoundException, AlreadyExistsException
from src.repositories.task_rep import TasksRepository
from src.repositories.user_rep import UsersRepository
from src.schemas.tasks_schemas import (
    TaskGetSchemas,
    TaskRequestSchemas,
    TaskCreateSchemas,
    TaskUserGetSchemas,
    TaskAPIRequestSchemas,
    TaskAPIResponseSchemas,
)
from src.utils.retry_client import retry_standard


class TaskService:

    def __init__(
        self,
        task_rep: TasksRepository,
        user_rep: UsersRepository,
        http_client: ReportServiceClient,
    ) -> None:
        self.task_rep = task_rep
        self.user_rep = user_rep
        self.http_client = http_client


    async def check_user_exists(self, user_id: uuid.UUID) -> None:
        user = await self.user_rep.one_or_none(id=user_id)
        if not user:
            logging.warning(f"User with id {user_id} not found")
            raise ObjectNotFoundException

    async def check_task_exists(self, task_id: uuid.UUID) -> None:
        task = await self.task_rep.one_or_none(id=task_id)
        if not task:
            logging.warning(f"Task with id {task_id} not found")
            raise ObjectNotFoundException

    async def check_title_exists(self, title: str) -> bool:
        task = await self.task_rep.one_or_none(title=title)
        return task

    async def get_all_with_parameters(self, user_id: uuid.UUID) -> list[TaskGetSchemas]:
        await self.check_user_exists(user_id=user_id)
        tasks = await self.task_rep.get_all_with_any_parameters(user_id=user_id)
        return tasks

    async def get_unrealized_tasks(self, user_id: uuid.UUID) -> list[TaskCreateSchemas]:
        await self.check_user_exists(user_id=user_id)
        tasks = await self.task_rep.get_all_with_any_parameters(user_id=user_id, done=False)
        return tasks

    async def get_one_or_none_with_relship(
        self,
        user_id: uuid.UUID,
        task_id: uuid.UUID,
    ) -> TaskUserGetSchemas:

        await self.check_user_exists(user_id=user_id)
        await self.check_task_exists(task_id=task_id)
        task = await self.task_rep.get_one_or_none_with_relship(id=task_id, user_id=user_id)
        return TaskUserGetSchemas.model_validate(task, from_attributes=True)

    async def add(
        self,
        user_id: uuid.UUID,
        tasks_info: list[TaskRequestSchemas],
    ) -> dict:
        await self.check_user_exists(user_id=user_id)

        tasks_added = []
        failed_tasks = []

        for task_info in tasks_info:
            try:
                task = await self.check_title_exists(title=task_info.title)
                if task:
                    logging.warning(f"Task '{task_info.title}' already exists")
                    raise AlreadyExistsException(detail=f"Task '{task_info.title}' already exists")

                task_id = uuid.uuid4()
                task_api_info = TaskAPIRequestSchemas(
                    user_id=user_id,
                    task_id=task_id,
                    **task_info.model_dump()
                )

                report = await self.http_client.get_report(task_api_info)

                full_data = {**task_info.model_dump(), **report.model_dump()}
                task_create = TaskCreateSchemas(
                    id=task_id,
                    user_id=user_id,
                    **full_data,
                )
                task = await self.task_rep.add(task_create)
                await self.task_rep.commit()

                tasks_added.append(task.title)

            except IntegrityError as ex:
                await self.task_rep.rollback()

                if isinstance(ex.orig.__cause__, UniqueViolationError):
                    logging.error(f"Unique violation for task '{task_info.title}'")
                    failed_tasks.append({
                        "title": task_info.title,
                        "error": "Task with this title already exists"
                    })
                elif isinstance(ex.orig.__cause__, ForeignKeyViolationError):
                    logging.error(f"Foreign key violation for task '{task_info.title}'")
                    failed_tasks.append({
                        "title": task_info.title,
                        "error": "Referenced object not found"
                    })
                else:
                    logging.error(f"Unknown integrity error: {ex}")
                    failed_tasks.append({
                        "title": task_info.title,
                        "error": "Database integrity error"
                    })
                continue

            except Exception as e:
                await self.task_rep.rollback()
                logging.error(f"{task_info.title} \n {str(e)}")
                failed_tasks.append({
                    "title": task_info.title,
                    "error": str(e)
                })
                continue

        return {
            "added": tasks_added,
            "failed_tasks": failed_tasks,
        }


    async def delete(
        self,
        user_id: uuid.UUID,
        task_id: uuid.UUID,
    ) -> TaskGetSchemas:

        await self.check_user_exists(user_id=user_id)
        await self.check_task_exists(task_id=task_id)
        task = await self.task_rep.delete(id=task_id, user_id=user_id)
        await self.task_rep.commit()
        return task
