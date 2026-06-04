import uuid
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
        "value": [
            {
            "title": "Купить бумагу",
            "description": "Заказать в офисмаге бумагу",
            "finish_date": '2026-05-21',
        },
            {
            "title": "Купить чернила",
            "description": "Магазин напротив пойти и купить",
            "finish_date": '2026-06-01',
        },
        ]
    },
    "2": {
        "summary": "Задача 2",
        "value": [
            {
            "title": "Купить билеты",
            "description": "Заказать билеты в Тайланд",
            "finish_date": '2026-05-01',
        },
        ]
    },
}


class TaskCreateSchemas(BaseModel):
    id: uuid.UUID = Field(..., description="ИД задачи")
    user_id: uuid.UUID = Field(..., description="ИД пользователя")
    title: str = Field(..., description="Короткое название задачи")
    description: str | None = Field(None, description="Описание задачи")
    finish_date: date = Field(..., description="Плановая дата выполнения задачи")
    done: bool = Field(False, description="Отметка о выполнении задачи")
    complexity: str = Field(..., description="Сложность выполняемой задачи")
    estimated_hours: float = Field(..., description="Время на выполнение задачи")
    priority: str = Field(..., description="Статус задачи")


class TaskGetSchemas(TaskCreateSchemas):
    ...


class TaskChangeSchemas(BaseModel):
    user_id: uuid.UUID | None = Field(None, description="Новое ИД пользователя")
    title: str | None = Field(None, description="Новое короткое название задачи")
    description: str | None = Field(None, description="Описание задачи")
    finish_date: date | None = Field(None, description="Новая плановая дата выполнения задачи")
    done: bool | None = Field(None, description="Отметка о выполнении задачи")


class TaskUserGetSchemas(BaseModel):
    id: uuid.UUID = Field(..., description="ИД задачи")
    user: UserGetSchemas = Field(..., description="Пользователь")
    title: str = Field(..., description="Короткое название задачи")
    description: str | None = Field(None, description="Описание задачи")
    finish_date: date = Field(..., description="Плановая дата выполнения задачи")
    done: bool = Field(False, description="Отметка о выполнении задачи")


class TaskAPIRequestSchemas(BaseModel):
    task_id: uuid.UUID = Field(..., description="ИД задачи")
    user_id: uuid.UUID = Field(..., description="ИД пользователя")
    title: str = Field(..., description="Короткое название задачи")
    description: str | None = Field(None, description="Описание задачи")
    finish_date: date = Field(..., description="Плановая дата выполнения задачи")


class TaskAPIResponseSchemas(BaseModel):
    complexity: str = Field(..., description="Сложность выполняемой задачи")
    estimated_hours: float = Field(..., description="Время на выполнение задачи")
    priority: str = Field(..., description="Статус задачи")


class TaskDeletedResponse(BaseModel):
    status: str = Field(default="OK", description="Статус операции")
    description: str = Field(description="Описание результата")
    delete_task_info: TaskGetSchemas = Field(description="Информация по удаленной задачи")


class TasksBulkCreatedResponse(BaseModel):
    success_tasks: str = Field(description="Список успешно добавленных задач")
    failed_tasks: str = Field(description="Список задач, которые не удалось добавить")