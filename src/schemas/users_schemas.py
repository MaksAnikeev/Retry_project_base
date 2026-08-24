import uuid
from datetime import datetime
from typing import Self

from pydantic import BaseModel, EmailStr, Field, model_validator, field_validator

from src.exceptions import AtLeastOneFieldRequiredException, EmptyRequestBodyException
from src.schemas.tasks_schemas import (
    TaskGetSchema,
    TaskRequestSchema,
    TaskUpdateSchema,
)


class UniqueTaskTitlesValidatorMixin:
    @model_validator(mode="after")
    def check_unique_task_titles(self) -> Self:
        tasks = getattr(self, "tasks", [])
        if not tasks:
            return self

        titles = [task.title for task in tasks if task.title]
        seen: set[str] = set()
        duplicates: list[str] = []

        for title in titles:
            if title in seen and title not in duplicates:
                duplicates.append(title)
            seen.add(title)

        if duplicates:
            raise ValueError(f"Duplicate task titles: {duplicates}")
        return self


class UserBase(BaseModel):
    email: EmailStr = Field(..., description="Адрес эл.почты")
    username: str | None = Field(None, description="Имя пользователя")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()


class UserRequestSchema(UserBase, UniqueTaskTitlesValidatorMixin):
    password: str = Field(..., description="Пароль")
    is_active: bool = Field(True, description="Статус пользователя")
    is_deleted: bool = Field(False, description="Пользователь удален")
    tasks: list[TaskRequestSchema] = Field(
        default_factory=list, description="Список задач для обновления"
    )

example_add_user_task = {
    "1": {
        "summary": "Макс",
        "value": {
            "email": "anikeev.mks@rambler.com",
            "username": "Maks",
            "password": "admin",
            "tasks": [
                {
                    "title": "Купить бумагу",
                    "description": "Заказать в офисмаге бумагу",
                    "finish_date": "2026-05-21",
                },
                {
                    "title": "Купить чернила",
                    "description": "Магазин напротив пойти и купить",
                    "finish_date": "2026-06-01",
                },
            ],
        },
    },
    "2": {
        "summary": "Лучиано",
        "value": {
            "email": "luchy@rambler.com",
            "username": "Maks",
            "password": "userik",
            "tasks": [],
        },
    },
}


class UserGetBase(BaseModel):
    id: uuid.UUID
    email: EmailStr = Field(..., description="Адрес эл.почты")
    username: str | None = Field(None, description="Имя пользователя")
    is_active: bool = Field(..., description="Статус пользователя")
    is_deleted: bool = Field(..., description="Пользователь удален")
    created_at: datetime = Field(..., description="Дата регистрации пользователя")
    updated_at: datetime | None = Field(None, description="Дата обновления информации о пользователе")

class UserTasksGetSchema(UserGetBase):
    tasks: list[TaskGetSchema] = Field(default_factory=list)


class UserTasksShortGetSchema(BaseModel):
    id: uuid.UUID
    email: EmailStr = Field(..., description="Адрес эл.почты")
    username: str | None = Field(None, description="Имя пользователя")
    is_active: bool = Field(..., description="Статус пользователя")
    is_deleted: bool = Field(..., description="Пользователь удален")

    tasks: list[TaskGetSchema] = Field(default_factory=list)


class UsersTasksPaginatedResponse(BaseModel):
    items: list[UserTasksShortGetSchema] = Field(description="Список элементов")
    next_cursor: datetime | None = Field(
        default=None, description="Курсор для следующей страницы (created_at последнего элемента)"
    )


class UserGetSchema(UserGetBase):
    pass


class UserUpdateWithTasksSchema(BaseModel, UniqueTaskTitlesValidatorMixin):
    id: uuid.UUID = Field(..., description="ID пользователя, которого обновляем")
    email: EmailStr | None = Field(None, description="Адрес эл.почты")
    username: str | None = Field(None, description="Имя пользователя")
    password: str | None = Field(None, description="Пароль")
    is_active: bool | None = Field(True, description="Статус пользователя")
    is_deleted: bool | None = Field(False, description="Пользователь удален")
    tasks: list[TaskUpdateSchema] = Field(
        default_factory=list, description="Список задач для обновления"
    )

    @model_validator(mode="after")
    def check_at_least_one_field(self):
        if not self.model_fields_set:
            raise EmptyRequestBodyException("At least one field must be passed")

        if all(value is None or value == "" for value in self.model_dump().values()):
            raise AtLeastOneFieldRequiredException("At least one field must be filled in")
        return self

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return v.lower().strip()

example_update_user_task = {
    "1": {
        "summary": "Изменить Макс",
        "value": {
            "id": "f13e4a44-351b-478c-8a54-17e029489626",
            "email": "anikeev.makson@rambler.com",
            "username": "Maksimus",
            "password": "1admin1",
            "tasks": [
                {
                    "id": "7ba83c9a-6a3e-4751-9018-d85b609e2332",
                    "title": "Купить бумагу2",
                    "description": "2222Заказать в офисмаге бумагу",
                    "finish_date": "2026-07-21",
                    "complexity": "hard",
                },
                {
                    "id": "3245e325-5e91-4d4b-9f8f-7ecb349c5a18",
                    "title": "Купить чернила2",
                    "description": "2222Магазин напротив пойти и купить",
                    "finish_date": "2026-07-01",
                },
                {
                    "title": "Новая задача для добавления",
                    "description": "Бла бла бла",
                    "finish_date": "2026-06-21",
                },
                {
                    "title": "Еще одна новая задача",
                    "description": "222222222",
                    "finish_date": "2026-07-02",
                },
            ],
        },
    },
    "2": {
        "summary": "Изменить Лучиано",
        "value": {"id": "86b86181-4a78-40b7-9426-a3d2d27f13df", "username": "Luciano", "tasks": []},
    },
    "3": {
        "summary": "Изменить только задачу",
        "value": {
            "id": "10cdd17b-1e74-4c56-84a8-231b9fa64000",
            "tasks": [
                {
                    "id": "7ba83c9a-6a3e-4751-9018-d85b609e2332",
                    "title": "Изменяю название",
                },
            ],
        },
    },
}



class DeletionResponseSchema(BaseModel):
    status: str = Field(default="success", description="Статус операции")
    message: str = Field(..., description="Сообщение о результате")
