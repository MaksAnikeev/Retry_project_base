from datetime import date

from pydantic import BaseModel, Field

from src.schemas.base_schema import ChangeBaseSchema
from src.schemas.users_schemas import UserGetSchemas


class TaskRequestSchemas(ChangeBaseSchema):
    title: str = Field(..., description="Короткое название задачи")
    description: str | None = Field(None, description="Описание задачи")
    finish_date: date = Field(..., description="Плановая дата выполнения задачи")


example_add_task = {
    "1": {
        "summary": "Задача 1",
        "value": {
            "title": "Купить бумагу",
            "description": "Заказать в офисмаге бумагу",
            "finish_date": '2026-05-01',
        },
    },
    "2": {
        "summary": "Задача 2",
        "value": {
            "title": "Купить билеты",
            "description": "Заказать билеты в Тайланд",
            "finish_date": '2026-05-01',
        },
    },
}


class TaskCreateSchemas(BaseModel):
    user_id: int = Field(..., description="ИД пользователя")
    title: str = Field(..., description="Короткое название задачи")
    description: str | None = Field(None, description="Описание задачи")
    finish_date: date = Field(..., description="Плановая дата выполнения задачи")
    done: bool = Field(False, description="Отметка о выполнении задачи")


class TaskGetSchemas(TaskCreateSchemas):
    id: int = Field(..., description="ИД задачи")


class TaskChangeSchemas(BaseModel):
    user_id: int | None = Field(None, description="Новое ИД пользователя")
    title: str | None = Field(None, description="Новое короткое название задачи")
    description: str | None = Field(None, description="Описание задачи")
    finish_date: date | None = Field(None, description="Новая плановая дата выполнения задачи")
    done: bool | None = Field(None, description="Отметка о выполнении задачи")


class TaskUserGetSchemas(BaseModel):
    id: int = Field(..., description="ИД задачи")
    user: UserGetSchemas = Field(..., description="Пользователь")
    title: str = Field(..., description="Короткое название задачи")
    description: str | None = Field(None, description="Описание задачи")
    finish_date: date = Field(..., description="Плановая дата выполнения задачи")
    done: bool = Field(False, description="Отметка о выполнении задачи")