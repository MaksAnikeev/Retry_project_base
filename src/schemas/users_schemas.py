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
    email: EmailStr = Field(..., description="Адрес эл.почты")
    username: str | None = Field(None, description="Имя пользователя")
    hashed_password: str = Field(..., description="Закодированный пароль")
    is_active: bool | None = Field(True, description="Статус пользователя")


class UserGetSchemas(BaseModel):
    id: int
    email: EmailStr = Field(..., description="Адрес эл.почты")
    username: str | None = Field(None, description="Имя пользователя")
    is_active: bool = Field(..., description="Статус пользователя")
    created_at: datetime = Field(..., description="Дата регистрации пользователя")
    updated_at: datetime = Field(
        ..., description="Дата обновления информации о пользователе")


class UserGetHashedPassword(BaseModel):
    id: int
    email: EmailStr = Field(..., description="Адрес эл.почты")
    hashed_password: str = Field(..., description="Закодированный пароль")

    model_config = {"from_attributes": True}
