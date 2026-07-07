from enum import Enum
from typing import Self
import uuid
from datetime import date

from pydantic import BaseModel, Field, model_validator


class ReportStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

    def __str__(self) -> str:
        return self.value


class TaskRequestSchema(BaseModel):
    title: str = Field(..., description="Короткое название задачи")
    description: str | None = Field(None, description="Описание задачи")
    finish_date: date = Field(..., description="Плановая дата выполнения задачи")

class TaskGetSchema(BaseModel):
    id: uuid.UUID
    title: str = Field(..., description="Короткое название задачи")
    description: str | None = Field(None, description="Описание задачи")
    finish_date: date = Field(..., description="Плановая дата выполнения задачи")
    done: bool = Field(False, description="Отметка о выполнении задачи")
    is_deleted: bool = Field(..., description="Задача удалена")
    report_status: str = Field(..., description="Статус обработки задачи: pending, completed, failed")
    complexity: str | None = Field(None, description="Сложность выполняемой задачи")
    estimated_hours: float | None = Field(None, description="Время на выполнение задачи")
    priority: str | None = Field(None, description="Статус важности задачи")


class TaskUpdateSchema(BaseModel):
    id: uuid.UUID = Field(..., description="ID задачи, которую обновляем")
    user_id: uuid.UUID | None = Field(None, description="Новое ИД пользователя")
    title: str | None = Field(None, description="Новое короткое название задачи")
    description: str | None = Field(None, description="Описание задачи")
    finish_date: date | None = Field(None, description="Новая плановая дата выполнения задачи")
    done: bool | None = Field(None, description="Отметка о выполнении задачи")
    complexity: str | None = Field(None, description="Сложность выполняемой задачи")
    estimated_hours: float | None = Field(None, description="Время на выполнение задачи")
    priority: str | None = Field(None, description="Статус задачи")


class TaskAPIRequestSchema(BaseModel):
    task_id: uuid.UUID = Field(..., description="ИД задачи")
    user_id: uuid.UUID = Field(..., description="ИД пользователя")
    title: str = Field(..., description="Короткое название задачи")
    description: str | None = Field(None, description="Описание задачи")
    finish_date: date = Field(..., description="Плановая дата выполнения задачи")


class TaskAPIResponseSchema(BaseModel):
    task_id: uuid.UUID = Field(..., description="ИД задачи")
    complexity: str = Field(..., description="Сложность выполняемой задачи")
    estimated_hours: float = Field(..., description="Время на выполнение задачи")
    priority: str = Field(..., description="Статус задачи")

    @model_validator(mode="after")
    def normalize(self) -> Self:
        self.complexity = self.complexity or "easy"
        self.estimated_hours = self.estimated_hours or 2.0
        self.priority = self.priority or "medium"
        return self


class TasksDeleteSchema(BaseModel):
    user_id: uuid.UUID = Field(..., description="ИД пользователя")
    task_id: uuid.UUID = Field(..., description="ИД задачи")


class DeleteTasksStatsSchema(BaseModel):
    deleted: int = Field(default=0, description="Количество удалённых задач")
    skipped: int = Field(default=0, description="Количество пропущенных задач")
