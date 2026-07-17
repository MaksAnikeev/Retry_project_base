from src.models import TaskORM
from src.schemas.tasks_schemas import (
    ReportStatus,
    TaskAPIRequestSchema,
    TaskAPIResponseSchema,
    TaskRequestSchema,
    TaskUpdateSchema,
)


def to_task_orm(task: TaskRequestSchema) -> TaskORM:
    return TaskORM(
        title=task.title,
        description=task.description,
        done=False,
        finish_date=task.finish_date,
        report_status=ReportStatus.PENDING.value,
    )


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


def update_task_fields(task_update_data: TaskUpdateSchema, task_orm: TaskORM) -> None:
    if task_update_data.title is not None:
        task_orm.title = task_update_data.title

    if task_update_data.description is not None:
        task_orm.description = task_update_data.description

    if task_update_data.finish_date is not None:
        task_orm.finish_date = task_update_data.finish_date

    if task_update_data.done is not None:
        task_orm.done = task_update_data.done

    if task_update_data.complexity is not None:
        task_orm.complexity = task_update_data.complexity

    if task_update_data.estimated_hours is not None:
        task_orm.estimated_hours = task_update_data.estimated_hours

    if task_update_data.priority is not None:
        task_orm.priority = task_update_data.priority
