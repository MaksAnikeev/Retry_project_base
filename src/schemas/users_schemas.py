import uuid
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from src.schemas.base_schema import ChangeBaseSchema


class UserRequestSchemas(ChangeBaseSchema):
    email: EmailStr = Field(..., description="Адрес эл.почты")
    username: str | None = Field(None, description="Имя пользователя")
    password: str = Field(..., description="Пароль")


example_add_user = {
    "1": {
        "summary": "Макс",
        "value": {
            "email": "anikeev.mks@rambler.com",
            "username": "Maks",
            "password": "admin",
        },
    },
    "2": {
        "summary": "Лучиано",
        "value": {"email": "luchy@rambler.com", "password": "userik"},
    },
}


class UserCreateSchemas(BaseModel):
    id: uuid.UUID
    email: EmailStr = Field(..., description="Адрес эл.почты")
    username: str | None = Field(None, description="Имя пользователя")
    hashed_password: str = Field(..., description="Закодированный пароль")
    is_active: bool | None = Field(True, description="Статус пользователя")
    is_deleted: bool | None = Field(False, description="Пользователь удален")


class UserGetSchemas(BaseModel):
    id: uuid.UUID
    email: EmailStr = Field(..., description="Адрес эл.почты")
    username: str | None = Field(None, description="Имя пользователя")
    is_active: bool = Field(..., description="Статус пользователя")
    is_deleted: bool = Field(..., description="Пользователь удален")
    created_at: datetime = Field(..., description="Дата регистрации пользователя")
    updated_at: datetime | None = Field(None, description="Дата обновления информации о пользователе")


class UserResponse(BaseModel):
    status: str = Field(default="OK", description="Статус операции")
    description: str = Field(description="Описание результата")
    user_info: UserGetSchemas = Field(description="Информация по юзеру")