import uuid
from datetime import date
from enum import Enum

from pydantic import BaseModel, Field


class ReportStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

    def __str__(self) -> str:
        return self.value


class TaskBase(BaseModel):
    title: str = Field(..., description="Короткое название задачи")
    description: str | None = Field(None, description="Описание задачи")
    finish_date: date = Field(..., description="Плановая дата выполнения задачи")


class TaskRequestSchema(TaskBase):
    done: bool = Field(False, description="Статус выполнения задачи")


class TaskGetSchema(TaskBase):
    id: uuid.UUID
    done: bool = Field(False, description="Отметка о выполнении задачи")
    is_deleted: bool = Field(..., description="Задача удалена")
    report_status: ReportStatus = Field(
        ..., description="Статус обработки задачи: pending, completed, failed"
    )
    complexity: str | None = Field(None, description="Сложность выполняемой задачи")
    estimated_hours: float | None = Field(None, description="Время на выполнение задачи")
    priority: str | None = Field(None, description="Статус важности задачи")


class TaskUpdateSchema(BaseModel):
    id: uuid.UUID | None = Field(None, description="ID задачи, которую обновляем")
    user_id: uuid.UUID | None = Field(None, description="Новое ИД пользователя")
    title: str | None = Field(None, description="Новое короткое название задачи")
    description: str | None = Field(None, description="Описание задачи")
    finish_date: date | None = Field(None, description="Новая плановая дата выполнения задачи")
    done: bool = Field(False, description="Отметка о выполнении задачи")
    complexity: str | None = Field(None, description="Сложность выполняемой задачи")
    estimated_hours: float | None = Field(None, description="Время на выполнение задачи")
    priority: str | None = Field(None, description="Статус задачи")


class TaskAPIRequestSchema(TaskBase):
    task_id: uuid.UUID = Field(..., description="ИД задачи", validation_alias="id")
    user_id: uuid.UUID = Field(..., description="ИД пользователя")


class TaskAPIResponseSchema(BaseModel):
    task_id: uuid.UUID = Field(..., description="ИД задачи")
    complexity: str = Field(default="easy", description="Сложность выполняемой задачи")
    estimated_hours: float = Field(default=2.0, description="Время на выполнение задачи")
    priority: str = Field(default="medium", description="Статус задачи")
