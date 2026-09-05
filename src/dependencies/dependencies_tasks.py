from typing import Annotated

from fastapi import Depends
from starlette.requests import Request

from src.clients.report_service_client import ReportServiceClient

from src.database.db import SessionDep
from src.dependencies.dependencies_uow import UowDep
from src.repositories.task_rep import TasksRepository
from src.repositories.user_rep import UsersRepository
from src.schemas.pagination_schema import PaginationParamsSchema
from src.services.user_task_service import UserTaskService


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


def get_user_task_service(
    user_rep: UserRepDep,
    report_client: ReportClientDep,
    uow: UowDep
) -> UserTaskService:
    return UserTaskService(
        user_rep=user_rep,
        report_client=report_client,
        uow=uow
    )

UserTaskServiceDep = Annotated[UserTaskService, Depends(get_user_task_service)]


PaginationDep = Annotated[PaginationParamsSchema, Depends()]
