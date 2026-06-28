import uuid

from fastapi import APIRouter, Body

from src.dependencies.dependencies import UserTaskServiceDep, PaginationDep
from src.schemas.users_schemas import (
    BulkDeletionResponseSchema,
    UserResponse,
    UserTasksDeleteSchema,
    UserTasksGetSchema,
    UserTasksShortGetSchema,
    UserUpdateWithTasksSchema,
    example_add_user_task, example_update_user_task, UserRequestSchema, UsersTasksPaginatedResponse,
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


@router.post("/user_task", summary="регистрация пользователя и добавление задач")
async def add_user_tasks(
    service: UserTaskServiceDep,
    user_data: UserRequestSchema = Body(openapi_examples=example_add_user_task),
) -> UserResponse:
    return await service.create_user_with_tasks(user_data=user_data)


@router.patch("", summary="Изменить информацию по пользователю или по его задачам")
async def edit_user_tasks(
    service: UserTaskServiceDep,
    update_data: UserUpdateWithTasksSchema = Body(openapi_examples=example_update_user_task)
) -> UserTasksGetSchema:
    return await service.update_user_and_tasks(update_data=update_data)


@router.delete("", summary="Удалить пользователей или его задачи по ИД")
async def del_users_tasks(
    service: UserTaskServiceDep, delete_info: UserTasksDeleteSchema
) -> BulkDeletionResponseSchema:
    return await service.delete_users_tasks(delete_info=delete_info)
