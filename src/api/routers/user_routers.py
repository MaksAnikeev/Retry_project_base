from fastapi import APIRouter, Body, Response

from src.api.dependencies import UserIDDep, DBDep
from src.exceptions import (
    AlreadyExistedException,
    ObjectNotFoundException,
    UserAlreadyExistedHTTPException,
    UserNotExistedHTTPException,
    IncorrectPasswordException,
    IncorrectPasswordHTTPException,
    EmptyAttributesException,
    EmptyPasswordHTTPException,
)
from src.schemas.users_schemas import (
    UserRequestSchemas,
    example_add_user,
)
from src.services.auth import AuthService



router = APIRouter(prefix="/user", tags=["Аутентификация и Авторизация"])


@router.get("/users", summary="Получить данные по всем пользователям")
async def get_users(
    db: DBDep,
):
    users = await db.users.get_all()
    return {"status": "success", "data": users, "details": None}


@router.get("/me", summary="🧑‍💻 Мой профиль")
async def who_are_me(
    user_id: UserIDDep,
    db: DBDep,
):
    user = await db.users.get_one(id=user_id)
    return {"status": "success", "data": user, "details": None}


@router.post("/add", summary="регистрация пользователя")
async def add_user(
    db: DBDep,
    user_info: UserRequestSchemas = Body(openapi_examples=example_add_user),
):
    try:
        new_user = await AuthService(db).add_user(user_info=user_info)

    except AlreadyExistedException:
        raise UserAlreadyExistedHTTPException

    except EmptyAttributesException:
        raise EmptyPasswordHTTPException

    await db.commit()
    return {
        "status": "OK",
        "description": f"Новый пользователь {new_user.username} успешно добавлен",
        "user_info": new_user,
    }


@router.post("/login", summary="аутентификация пользователя")
async def user_login(
    response: Response,
    db: DBDep,
    user_info: UserRequestSchemas = Body(openapi_examples=example_add_user),
):
    try:
        access_token = await AuthService(db).get_user_with_hashed_password(
            user_info=user_info
        )
    except ObjectNotFoundException:
        raise UserNotExistedHTTPException
    except IncorrectPasswordException:
        raise IncorrectPasswordHTTPException
    response.set_cookie("access_token", access_token)

    return {
        "status": "OK",
        "description": "JWT token успешно создан",
        "access_token": access_token,
    }


@router.post("/logout", summary="Удаление токена доступа. Разлогиневание")
async def logout(response: Response):
    response.delete_cookie(
        "access_token", httponly=True, secure=False, samesite="lax", path="/"
    )
    return {
        "status": "success",
        "message": "Вы успешно вышли из системы",
    }

@router.delete("/delete", summary="Удаление пользователя")
async def user_delete(
    user_id: UserIDDep,
    db: DBDep,
    id_to_delete: int,
    ):
    try:
        user = await db.users.delete(id=id_to_delete)
    except ObjectNotFoundException:
        raise UserNotExistedHTTPException

    await db.commit()
    return {"status": "success", "data": user, "details": None}