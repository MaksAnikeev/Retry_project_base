from src.models import TaskORM
from src.schemas.tasks_schemas import TaskRequestSchema, TaskAPIRequestSchema, ReportStatus


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