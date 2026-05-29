import uuid

from fastapi import APIRouter, Body

from src.api.dependencies import TaskServiceDep
from src.schemas.tasks_schemas import (
    example_add_task,
    TaskRequestSchemas,
    TaskGetSchemas, TaskCreateSchemas, TaskUserGetSchemas,
)

router = APIRouter(prefix="/tasks", tags=["Задачи"])


@router.get("", summary="Получить все задачи пользователя")
async def get_tasks(
    user_id: uuid.UUID,
    task_service: TaskServiceDep
) -> list[TaskGetSchemas] :
    tasks = await task_service.get_all_with_parameters(user_id=user_id)
    return tasks

@router.get("/{task_id}", summary="Получить данные по задаче")
async def get_task(
    user_id: uuid.UUID,
    task_id: uuid.UUID,
    task_service: TaskServiceDep,
) -> TaskUserGetSchemas:
    task = await task_service.get_one_or_none_with_relship(
        user_id=user_id,
        task_id=task_id,
    )
    return task


@router.post("", summary="Добавить задачу пользователю")
async def add_task(
    user_id: uuid.UUID,
    task_service: TaskServiceDep,
    task_info: TaskRequestSchemas = Body(openapi_examples=example_add_task),
) -> dict:
    task: TaskGetSchemas = await task_service.add(
        user_id=user_id, task_info=task_info
    )
    return {
        "status": "OK",
        "description": f"Задача с названием {task.title} успешно добавлен пользователю с ид {task.user_id}.",
        "task_info": task,
    }


@router.delete("/{task_id}", summary="Удалить задачу по ИД")
async def del_task(
    user_id: uuid.UUID,
    task_id: uuid.UUID,
    task_service: TaskServiceDep,
) -> dict:
    task = await task_service.delete(user_id=user_id, task_id=task_id)
    return {
        "status": "OK",
        "description": f"Задача с ид {task.id} удалена.",
        "delete_task_info": task,
    }