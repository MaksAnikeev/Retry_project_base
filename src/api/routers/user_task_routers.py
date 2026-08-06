import uuid

from fastapi import APIRouter, Body, Query

from src.dependencies.dependencies_tasks import PaginationDep, UserTaskServiceDep
from src.schemas.users_schemas import (
    UserRequestSchema,
    UsersTasksPaginatedResponse,
    DeletionResponseSchema,
    UserTasksGetSchema,
    UserUpdateWithTasksSchema,
    example_add_user_task,
    example_update_user_task,
)

router = APIRouter(prefix="/user_tasks", tags=["UserTasks"])


@router.get("", summary="Получить данные по всем пользователям с их задачами")
async def get_users(
    service: UserTaskServiceDep,
    pagination: PaginationDep,
) -> UsersTasksPaginatedResponse:
    return await service.get_all_users(pagination)


@router.get("/users/{user_id}", summary="Данные по пользователю")
async def get_user(
    user_id: uuid.UUID,
    service: UserTaskServiceDep,
) -> UserTasksGetSchema:
    return await service.get_user_by_id(user_id=user_id)


@router.post("", summary="регистрация пользователя и добавление задач")
async def add_user_tasks(
    service: UserTaskServiceDep,
    user_data: UserRequestSchema = Body(openapi_examples=example_add_user_task),
) -> UserTasksGetSchema:
    return await service.create_user_with_tasks(user_data=user_data)


@router.patch("", summary="Изменить информацию по пользователю, добавить или изменить его задачи")
async def edit_user_tasks(
    service: UserTaskServiceDep,
    update_data: UserUpdateWithTasksSchema = Body(openapi_examples=example_update_user_task),
) -> UserTasksGetSchema:
    return await service.update_user_and_tasks(update_data=update_data)


@router.delete(
    "/users/{user_id}",
    summary="Удалить пользователя или его конкретные задачи"
)
async def delete_user_or_tasks(
    service: UserTaskServiceDep,
    user_id: uuid.UUID,
    task_ids: set[uuid.UUID] | None = Query(
        default=None,
        description="Список ID задач для удаления. Если не указан, будет удален сам пользователь (и все его задачи)."
    )
) -> DeletionResponseSchema:
    return await service.delete_user_or_tasks(
        user_id=user_id,
        task_ids=task_ids
    )