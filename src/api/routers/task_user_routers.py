import uuid

from fastapi import APIRouter, Body

from src.api.dependencies import TaskServiceDep
from src.schemas.tasks_schemas import (
    example_add_task,
    TaskRequestSchemas,
    TaskGetSchemas,
    TaskUserGetSchemas,
    TaskDeletedResponse,
    TasksBulkCreatedResponse,
)

from src.api.dependencies import UserServiceDep
from src.schemas.users_schemas import (
    UserRequestSchemas,
    example_add_user,
    UserGetSchemas,
    UserResponse,
)
from src.utils.logging_decorator import log

router = APIRouter(prefix="/user_tasks", tags=["UserTasks"])


@router.get("/users", summary="Получить данные по всем пользователям")
@log("get_users")
async def get_users(
    user_service: UserServiceDep,
) -> list[UserGetSchemas]:
    users = await user_service.get_all()
    return users


@router.get("/users/{user_id}", summary="Данные по пользователю")
@log("get_user")
async def get_user(
    user_id: uuid.UUID,
    user_service: UserServiceDep,
) -> UserGetSchemas:
    user = await user_service.get_one_or_none(user_id=user_id)
    return user


@router.post("/users", summary="регистрация пользователя")
@log("add_user")
async def add_user(
    user_service: UserServiceDep,
    user_info: UserRequestSchemas = Body(openapi_examples=example_add_user),
) -> UserResponse:
    new_user = await user_service.add_user(user_info=user_info)
    return UserResponse(
        status="OK",
        description=f"Пользователь с ид {new_user.id} успешно добавлен.",
        user_info=new_user,
    )


@router.delete("/users/{user_id}", summary="Удаление пользователя")
@log("user_delete")
async def user_delete(
    user_id: uuid.UUID,
    user_service: UserServiceDep,
    ) -> UserResponse:
    user = await user_service.delete(user_id=user_id)
    return UserResponse(
        status="OK",
        description=f"Пользователь с ид {user.id} удален.",
        user_info=user,
    )


@router.get("/tasks", summary="Получить все задачи пользователя")
@log("get_tasks")
async def get_tasks(
    user_id: uuid.UUID,
    task_service: TaskServiceDep
) -> list[TaskGetSchemas] :
    tasks = await task_service.get_all_with_parameters(user_id=user_id)
    return tasks

@router.get("tasks/{task_id}", summary="Получить данные по задаче")
@log("get_task")
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


@router.post("/tasks", summary="Добавить задачи пользователю")
@log("add_tasks")
async def add_task(
    user_id: uuid.UUID,
    task_service: TaskServiceDep,
    tasks_info: list[TaskRequestSchemas] = Body(openapi_examples=example_add_task),
) -> TasksBulkCreatedResponse:

    result = await task_service.add(
        user_id=user_id, tasks_info=tasks_info
    )
    tasks_added = result["added"]
    failed_tasks = result["failed_tasks"]
    failed_tasks_str = "\n".join([str(ft) for ft in failed_tasks])

    return TasksBulkCreatedResponse(
        success_tasks=f"Успешно добавлено {len(tasks_added)} задач: {' \n '.join(tasks_added)}",
        failed_tasks=f"Не добавлено {len(failed_tasks)} задач: \n {failed_tasks_str}",
    )


@router.delete("/tasks/{task_id}", summary="Удалить задачу по ИД")
@log("del_task")
async def del_task(
    user_id: uuid.UUID,
    task_id: uuid.UUID,
    task_service: TaskServiceDep,
) -> TaskDeletedResponse:
    task = await task_service.delete(user_id=user_id, task_id=task_id)
    return TaskDeletedResponse(
        status="OK",
        description=f"Задача с ид {task.id} удалена.",
        delete_task_info=task,
    )