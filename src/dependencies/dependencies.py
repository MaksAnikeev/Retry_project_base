from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from src.db import get_session
from src.repositories.task_rep import TasksRepository
from src.repositories.user_rep import UsersRepository
from src.schemas.base_schema import PaginationParamsSchema
from src.services.user_task_service import UserTaskService
from src.clients.report_http_client import ReportServiceClient


SessionDep = Annotated[AsyncSession, Depends(get_session)]

def get_task_rep(session: SessionDep) -> TasksRepository:
    return TasksRepository(session=session)

TaskRepDep = Annotated[TasksRepository, Depends(get_task_rep)]


def get_user_rep(session: SessionDep) -> UsersRepository:
    return UsersRepository(session=session)

UserRepDep = Annotated[UsersRepository, Depends(get_user_rep)]


def get_report_client(request: Request) -> ReportServiceClient:
    client = getattr(request.app.state, "report_client", None)
    if client is None:
        raise RuntimeError("ReportServiceClient not initialized")
    return client

ReportClientDep = Annotated[ReportServiceClient, Depends(get_report_client)]


PaginationDep = Annotated[PaginationParamsSchema, Depends()]

def get_user_task_service(
    user_rep: UserRepDep,
    http_client: ReportClientDep,
) -> UserTaskService:
    return UserTaskService(
        user_rep=user_rep,
        http_client=http_client,
    )

UserTaskServiceDep = Annotated[UserTaskService, Depends(get_user_task_service)]
