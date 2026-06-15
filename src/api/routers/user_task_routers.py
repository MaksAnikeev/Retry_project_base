import uuid

from fastapi import APIRouter, Body, Depends

from src.api.dependencies import UserTaskServiceDep
from src.schemas.base_schema import PaginationParamsSchema
from src.schemas.tasks_schemas import TaskUserGetSchema
from src.schemas.users_schemas import (
    BulkDeletionResponseSchema,
    UserResponse,
    UserTasksDeleteSchema,
    UserTasksGetSchema,
    UserTasksShortGetSchema,
    UserUpdateWithTasksSchema,
    example_add_user_task, example_update_user_task, UserRequestSchema,
)
from src.utils.logging_decorator import log

router = APIRouter(prefix="/user_tasks", tags=["UserTasks"])


@router.get("", summary="Получить данные по всем пользователям с их задачами")
@log("get_users")
async def get_users(
    service: UserTaskServiceDep,
    pagination: PaginationParamsSchema = Depends(PaginationParamsSchema),
) -> list[UserTasksShortGetSchema]:
    users = await service.get_all_users(pagination)
    return users


@router.get("/users/{user_id}", summary="Данные по пользователю")
@log("get_user")
async def get_user(
    user_id: uuid.UUID,
    service: UserTaskServiceDep,
) -> UserTasksGetSchema:
    user = await service.get_user_by_id(user_id=user_id)
    return user


@router.get("tasks/{task_id}", summary="Получить данные по задаче")
@log("get_task")
async def get_task(
    task_id: uuid.UUID,
    service: UserTaskServiceDep,
) -> TaskUserGetSchema:
    task = await service.get_task_by_id(task_id=task_id)
    return task


@router.post("/user_task", summary="регистрация пользователя и добавление задач")
@log("add_user_tasks")
async def add_user_tasks(
    service: UserTaskServiceDep,
    user_data: UserRequestSchema = Body(openapi_examples=example_add_user_task),
) -> UserResponse:
    user_tasks_info = await service.upsert_user_with_tasks(user_data=user_data)
    return user_tasks_info


@router.patch("", summary="Изменить информацию по пользователю или по его задачам")
@log("edit_user_tasks")
async def edit_user_tasks(
    service: UserTaskServiceDep,
    update_data: UserUpdateWithTasksSchema = Body(openapi_examples=example_update_user_task)
) -> UserTasksGetSchema:
    changed_user_tasks = await service.update_user_and_tasks(update_data=update_data)
    return changed_user_tasks


@router.delete("", summary="Удалить пользователей или его задачи по ИД")
@log("del_users_tasks")
async def del_users_tasks(
    service: UserTaskServiceDep, delete_info: UserTasksDeleteSchema
) -> BulkDeletionResponseSchema:
    deleted_info = await service.delete_users_tasks(delete_info=delete_info)
    return deleted_info
