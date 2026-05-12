from src.schemas.tasks_schemas import (
    TaskGetSchemas,
    TaskRequestSchemas,
    TaskCreateSchemas,
)
from src.services.base_service import BaseService


class TaskService(BaseService):
    async def get_all_with_parameters(self, user_id: int) -> list[TaskGetSchemas]:
        await self.check_user_or_task_exists(user_id=user_id)
        tasks = await self.db.tasks.get_all_with_parameters(user_id=user_id)
        return tasks

    async def get_unrealized_tasks(self, user_id: int) -> list[TaskCreateSchemas]:
        await self.check_user_or_task_exists(user_id=user_id)
        tasks = await self.db.tasks.get_all_with_parameters(user_id=user_id, done=False)
        return tasks

    async def get_one_or_none_with_relship(
        self,
        user_id: int,
        task_id: int,
    ) -> TaskGetSchemas:

        await self.check_user_or_task_exists(user_id=user_id, task_id=task_id)
        task = await self.db.tasks.get_one_or_none_with_relship(
            id=task_id, user_id=user_id
        )
        return task

    async def add(
        self,
        user_id: int,
        task_info: TaskRequestSchemas,
    ) -> TaskGetSchemas:

        await self.check_user_or_task_exists(user_id=user_id)
        _task_info = TaskCreateSchemas(user_id=user_id, **task_info.model_dump())
        task: TaskGetSchemas = await self.db.tasks.add(_task_info)
        return task

    async def delete(
        self,
        user_id: int,
        task_id: int,
    ) -> TaskGetSchemas:

        await self.check_user_or_task_exists(user_id=user_id, task_id=task_id)
        task = await self.db.tasks.delete(id=task_id, user_id=user_id)
        return task
