import uuid
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from src.schemas.base_schema import ChangeBaseSchema
from src.schemas.tasks_schemas import TaskCreateSchema, TaskGetSchema, TaskUpdateSchema, TaskRequestSchema, \
    TasksDeleteSchema


class UserRequestSchema(BaseModel):
    email: EmailStr = Field(..., description="Адрес эл.почты")
    username: str | None = Field(None, description="Имя пользователя")
    password: str = Field(..., description="Пароль")
    tasks: list[TaskRequestSchema] = Field(default_factory=list, description="Список задач для обновления")

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
                "finish_date": '2026-05-21',
                },
                {
                "title": "Купить чернила",
                "description": "Магазин напротив пойти и купить",
                "finish_date": '2026-06-01',
                },
            ]
        },
    },
    "2": {
        "summary": "Лучиано",
        "value": {
            "email": "luchy@rambler.com",
            "username": "Maks",
            "password": "userik",
            "tasks": []
        },
    },
    "3": {
        "summary": "Добавить задачи Макс",
        "value": {
            "email": "anikeev.mks@rambler.com",
            "password": "admin",
            "tasks": [
                {
                "title": "Купить бумагу",
                "description": "Заказать в офисмаге бумагу",
                "finish_date": '2026-05-21',
                },
                {
                "title": "Купить чернила2",
                "description": "222222222",
                "finish_date": '2026-06-02',
                },
            ]
        },
    },
}


class UserTasksCreateSchema(BaseModel):
    id: uuid.UUID
    email: EmailStr = Field(..., description="Адрес эл.почты")
    username: str | None = Field(None, description="Имя пользователя")
    hashed_password: str = Field(..., description="Закодированный пароль")
    is_active: bool | None = Field(True, description="Статус пользователя")
    is_deleted: bool | None = Field(False, description="Пользователь удален")

    tasks: list[TaskCreateSchema] = Field(default_factory=list)


class UserTasksGetSchema(BaseModel):
    id: uuid.UUID
    email: EmailStr = Field(..., description="Адрес эл.почты")
    username: str | None = Field(None, description="Имя пользователя")
    is_active: bool = Field(..., description="Статус пользователя")
    is_deleted: bool = Field(..., description="Пользователь удален")
    created_at: datetime = Field(..., description="Дата регистрации пользователя")
    updated_at: datetime | None = Field(None, description="Дата обновления информации о пользователе")

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
        default=None,
        description="Курсор для следующей страницы (created_at последнего элемента)"
    )


class UserGetSchema(BaseModel):
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

class UserUpdateWithTasksSchema(ChangeBaseSchema):
    id: uuid.UUID = Field(..., description="ID пользователя, которого обновляем")
    email: EmailStr | None = Field(None, description="Адрес эл.почты")
    username: str | None = Field(None, description="Имя пользователя")
    password: str | None = Field(None, description="Пароль")
    is_active: bool | None = Field(True, description="Статус пользователя")
    is_deleted: bool | None = Field(False, description="Пользователь удален")
    tasks: list[TaskUpdateSchema] = Field(default_factory=list, description="Список задач для обновления")

example_update_user_task = {
    "1": {
        "summary": "Изменить Макс",
        "value": {
            "id": "10cdd17b-1e74-4c56-84a8-231b9fa64000",
            "email": "anikeev.maks@rambler.com",
            "username": "Maksimus",
            "password": "1admin1",
            "tasks": [
                {
                "id": "34e79c79-a84b-46f5-9636-7043ca196b39",
                "title": "Купить бумагу2",
                "description": "2222Заказать в офисмаге бумагу",
                "finish_date": '2026-05-21',
                },
                {
                "id": "f0ea88c5-4b9b-4e6c-8f30-02d10259be5c",
                "title": "Купить чернила2",
                "description": "2222Магазин напротив пойти и купить",
                "finish_date": '2026-06-01',
                },
            ]
        },
    },
    "2": {
        "summary": "Изменить Лучиано",
        "value": {
            "id": "86b86181-4a78-40b7-9426-a3d2d27f13df",
            "username": "Luciano",
            "tasks": []
        },
    },
    "3": {
        "summary": "Изменить только задачу",
        "value": {
            "id": "10cdd17b-1e74-4c56-84a8-231b9fa64000",
            "tasks": [
                {
                "id": "f485029f-9a25-48b7-8f9f-9ea04368ccd3",
                "title": "Изменяю название",
                },
            ]
        },
    },
}

class UserTasksDeleteSchema(BaseModel):
    delete_users: list[uuid.UUID] = Field(default_factory=list, description="ID пользователей для удаления")
    delete_tasks: list[TasksDeleteSchema] = Field(default_factory=list, description="Задачи для удаления")


class BulkDeletionResponseSchema(BaseModel):
    status: str = Field(default="success", description="Статус выполнения операции")
    message: str = Field(description="Человекочитаемое сообщение о результате")
    deleted_users_count: int = Field(default=0, description="Количество удаленных пользователей")
    deleted_tasks_count: int = Field(default=0, description="Количество удаленных задач")

UserTasksCreateSchema.model_rebuild()
