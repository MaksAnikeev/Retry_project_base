from fastapi import APIRouter, Body

from src.api.dependencies import DBDep, UserIDDep
from src.exceptions import (
    TooLongParameterException,
    UserNotFoundHTTPException,
    UserNotFoundException,
    TaskNotFoundException,
    TaskNotFoundHTTPException,
    TooLongParameterHTTPException, AlreadyExistedException, TaskAlreadyExistedHTTPException, ObjectNotFoundException,
    UserTaskNotFoundHTTPException,
)
from src.schemas.tasks_schemas import (
    example_add_task,
    TaskRequestSchemas,
    TaskGetSchemas,
)

from src.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["Задачи"])


@router.get("/{user_id}/tasks", summary="Получить все задачи пользователя")
async def get_tasks(user_id: int, db: DBDep):
    try:
        tasks = await TaskService(db).get_all_with_parameters(user_id=user_id)
    except UserNotFoundException:
        raise UserNotFoundHTTPException

    return {"status": "success", "tasks": tasks, "details": None}


@router.get("/{user_id}/unrealized_tasks", summary="Получить все невыполненные задачи пользователя")
async def get_unrealized_tasks(user_id: int, db: DBDep):
    try:
        unrealized_tasks = await TaskService(db).get_unrealized_tasks(user_id=user_id)
    except UserNotFoundException:
        raise UserNotFoundHTTPException

    return {"status": "success", "tasks": unrealized_tasks, "details": None}


@router.get("/me", summary="Получить мои задачи")
async def get_my_tasks(
        user_id: UserIDDep,
        db: DBDep,
):
    try:
        tasks = await TaskService(db).get_all_with_parameters(user_id=user_id)
    except UserNotFoundException:
        raise UserNotFoundHTTPException

    return {"status": "success", "tasks": tasks, "details": None}


@router.get("/{user_id}/tasks/{task_id}", summary="Получить данные по задаче")
async def get_task(
    user_id: int,
    task_id: int,
    db: DBDep,
):
    try:
        task = await TaskService(db).get_one_or_none_with_relship(
            user_id=user_id,
            task_id=task_id,
        )
    except UserNotFoundException:
        raise UserNotFoundHTTPException
    except TaskNotFoundException:
        raise TaskNotFoundHTTPException
    except ObjectNotFoundException:
        raise UserTaskNotFoundHTTPException

    return {"status": "success", "task": task, "detail": None}


@router.post("/{user_id}/task", summary="Добавить задачу пользователю")
async def add_task(
    user_id: int,
    db: DBDep,
    task_info: TaskRequestSchemas = Body(openapi_examples=example_add_task),
):
    try:
        task: TaskGetSchemas = await TaskService(db).add(
            user_id=user_id, task_info=task_info
        )
    except UserNotFoundException:
        raise UserNotFoundHTTPException
    except AlreadyExistedException:
        raise TaskAlreadyExistedHTTPException

    await db.commit()
    return {
        "status": "OK",
        "description": f"Задача с названием {task.title} успешно добавлен пользователю с ид {task.user_id}.",
        "task_info": task,
    }


@router.delete("/{user_id}/task/{task_id}", summary="Удалить задачу по ИД")
async def del_task(
    user_id: int,
    task_id: int,
    db: DBDep,
):
    try:
        task = await TaskService(db).delete(user_id=user_id, task_id=task_id)
    except UserNotFoundException:
        raise UserNotFoundHTTPException
    except TaskNotFoundException:
        raise TaskNotFoundHTTPException
    except TooLongParameterException:
        raise TooLongParameterHTTPException
    except ObjectNotFoundException:
        raise UserTaskNotFoundHTTPException

    await db.commit()
    return {
        "status": "OK",
        "description": f"Задача с ид {task.id} удалена.",
        "delete_task_info": task,
    }