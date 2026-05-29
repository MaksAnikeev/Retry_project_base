import uuid

from fastapi import APIRouter, Body

from src.api.dependencies import UserServiceDep
from src.schemas.users_schemas import (
    UserRequestSchemas,
    example_add_user, UserGetSchemas,
)

router = APIRouter(prefix="/user", tags=["Users"])


@router.get("", summary="Получить данные по всем пользователям")
async def get_users(
    user_service: UserServiceDep,
) -> list[UserGetSchemas]:
    users = await user_service.get_all()
    return users


@router.get("/{user_id}", summary="Данные по пользователю")
async def get_user(
    user_id: uuid.UUID,
    user_service: UserServiceDep,
) -> UserGetSchemas:
    user = await user_service.get_one_or_none(user_id=user_id)
    return user


@router.post("", summary="регистрация пользователя")
async def add_user(
    user_service: UserServiceDep,
    user_info: UserRequestSchemas = Body(openapi_examples=example_add_user),
) -> dict:
    new_user = await user_service.add_user(user_info=user_info)
    return {
        "status": "OK",
        "description": f"Новый пользователь {new_user.username} успешно добавлен",
        "user_info": new_user,
    }


@router.delete("/{user_id}", summary="Удаление пользователя")
async def user_delete(
    user_id: uuid.UUID,
    user_service: UserServiceDep,
    ):
    user = await user_service.delete(user_id=user_id)
    return {"status": "success", "data": user, "details": None}