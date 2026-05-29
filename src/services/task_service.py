import uuid

from src.clients.http_client import TaskServiceClient
from src.exceptions.exceptions import AlreadyExistedException, TaskAlreadyExistedHTTPException, \
    ObjectNotFoundHTTPException
from src.repositories.task_rep import TasksRepository
from src.repositories.user_rep import UsersRepository
from src.schemas.tasks_schemas import (
    TaskGetSchemas,
    TaskRequestSchemas,
    TaskCreateSchemas, TaskUserGetSchemas, TaskAPIRequestSchemas, TaskAPIResponseSchemas,
)
from src.utils.circuit_breaker import CircuitBreaker
from src.utils.retry_client import retry_standard


class TaskService:

    def __init__(
        self,
        task_rep: TasksRepository,
        user_rep: UsersRepository,
        http_client: TaskServiceClient,
        circuit_breaker: CircuitBreaker | None = None,
    ) -> None:
        self.task_rep = task_rep
        self.user_rep = user_rep
        self.http_client = http_client
        self.circuit_breaker = circuit_breaker


    async def check_user_exists(self, user_id: uuid.UUID) -> bool:
        user = await self.user_rep.one_or_none(id=user_id)
        if not user:
            raise ObjectNotFoundHTTPException

    async def check_task_exists(self, task_id: uuid.UUID) -> bool:
        task = await self.task_rep.one_or_none(id=task_id)
        if not task:
            raise ObjectNotFoundHTTPException

    async def get_all_with_parameters(self, user_id: uuid.UUID) -> list[TaskGetSchemas]:
        await self.check_user_exists(user_id=user_id)
        tasks = await self.task_rep.get_all_with_parameters(user_id=user_id)
        return tasks

    async def get_unrealized_tasks(self, user_id: uuid.UUID) -> list[TaskCreateSchemas]:
        await self.check_user_exists(user_id=user_id)
        tasks = await self.task_rep.get_all_with_parameters(user_id=user_id, done=False)
        return tasks

    async def get_one_or_none_with_relship(
        self,
        user_id: uuid.UUID,
        task_id: uuid.UUID,
    ) -> TaskUserGetSchemas:

        await self.check_user_exists(user_id=user_id)
        await self.check_task_exists(task_id=task_id)
        task= await self.task_rep.get_one_or_none_with_relship(id=task_id, user_id=user_id)
        return task

    async def get_report_with_retry(self, task_info: TaskAPIRequestSchemas) -> TaskAPIResponseSchemas:
        """
        Получить невыполненные задачи из внешнего сервиса с использованием retry и Circuit Breaker

        Порядок вызова:
        1. Circuit Breaker проверяет состояние
        2. Если CLOSED/HALF_OPEN → выполняет запрос с retry
        3. При успехе → сбрасывает счётчик ошибок
        4. При ошибке → увеличивает счётчик, может открыть цепь
        """
        retryable_get_report = retry_standard(self.http_client.get_report)
        return await self.circuit_breaker.call(
            retryable_get_report,
            task_info
        )

    async def add(
        self,
        user_id: uuid.UUID,
        task_info: TaskRequestSchemas,
    ) -> TaskGetSchemas:
        await self.check_user_exists(user_id=user_id)

        task_id = uuid.uuid4()
        task_api_info = TaskAPIRequestSchemas(
            user_id=user_id,
            task_id=task_id,
            **task_info.model_dump()
        )
        report = await self.get_report_with_retry(task_api_info)

        full_data = {**task_info.model_dump(), **report.model_dump()}
        task_create = TaskCreateSchemas(
            id=task_id,
            user_id=user_id,
            **full_data,
        )

        try:
            task = await self.task_rep.add(task_create)
        except AlreadyExistedException:
            raise TaskAlreadyExistedHTTPException
        await self.task_rep.commit()
        return task

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
