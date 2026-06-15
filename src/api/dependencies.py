from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_session
from src.repositories.task_rep import TasksRepository
from src.repositories.user_rep import UsersRepository
from src.services.user_task_service import UserTaskService
from src.clients.report_http_client import ReportServiceClient


_report_client: ReportServiceClient | None = None


SessionDep = Annotated[AsyncSession, Depends(get_session)]

# ==================== Repositories ====================
def get_task_rep(session: SessionDep) -> TasksRepository:
    return TasksRepository(session=session)

TaskRepDep = Annotated[TasksRepository, Depends(get_task_rep)]

def get_user_rep(session: SessionDep) -> UsersRepository:
    return UsersRepository(session=session)

UserRepDep = Annotated[UsersRepository, Depends(get_user_rep)]


# ==================== HTTP Client ====================
def get_report_client() -> ReportServiceClient:
    return _report_client

ReportClientDep = Annotated[ReportServiceClient, Depends(get_report_client)]


# ==================== Services ====================
def get_user_task_service(
    task_rep: TaskRepDep,
    user_rep: UserRepDep,
    http_client: ReportClientDep,
) -> UserTaskService:
    return UserTaskService(
        task_rep=task_rep,
        user_rep=user_rep,
        http_client=http_client,
    )

UserTaskServiceDep = Annotated[UserTaskService, Depends(get_user_task_service)]
