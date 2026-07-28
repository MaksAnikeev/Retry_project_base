from src.models import TaskORM, UserORM
from src.schemas.tasks_schemas import (
    ReportStatus,
    TaskAPIRequestSchema,
    TaskAPIResponseSchema,
    TaskRequestSchema,
    TaskUpdateSchema,
)
from src.schemas.users_schemas import UserUpdateWithTasksSchema


def to_task_orm(task: TaskRequestSchema) -> TaskORM:
    data = task.model_dump()
    return TaskORM(**data)


def to_task_api_request(task: TaskORM) -> TaskAPIRequestSchema:
    return TaskAPIRequestSchema(
        task_id=task.id,
        user_id=task.user_id,
        title=task.title,
        description=task.description,
        finish_date=task.finish_date,
    )


def add_report_to_task(task: TaskORM, report: TaskAPIResponseSchema) -> None:
    task.complexity = report.complexity
    task.estimated_hours = report.estimated_hours
    task.priority = report.priority
    task.report_status = ReportStatus.COMPLETED.value


def update_tasks_fields(tasks_update_data: list[TaskUpdateSchema], user: UserORM) -> None:
    existing_tasks_map = {task.id: task for task in user.tasks}
    for task_update in tasks_update_data:
        task_orm = existing_tasks_map[task_update.id]
        update_dict = task_update.model_dump(
            exclude_unset=True,
        )
        for field, value in update_dict.items():
            setattr(task_orm, field, value)


def split_tasks_by_type(
        update_data: UserUpdateWithTasksSchema
    ) -> tuple[list[TaskORM], list[TaskUpdateSchema]]:

        tasks_to_add_orm = []
        tasks_to_update = []
        for task_data in update_data.tasks:
            if task_data.id:
                tasks_to_update.append(task_data)
            else:
                valid_task = TaskRequestSchema.model_validate(task_data.model_dump())
                tasks_to_add_orm.append(to_task_orm(valid_task))
        return tasks_to_add_orm, tasks_to_update
