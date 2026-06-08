from typing import Annotated
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

from src.db import async_session_factory
from src.repositories.task_rep import TasksRepository
from src.repositories.user_rep import UsersRepository
from src.services.task_service import TaskService
from src.services.user_service import UserService
from src.clients.report_http_client import ReportServiceClient



_report_client: ReportServiceClient | None = None


async def get_session() -> AsyncGenerator[AsyncSession]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

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
def get_task_service(
    task_rep: TaskRepDep,
    user_rep: UserRepDep,
    http_client: ReportClientDep,
) -> TaskService:
    return TaskService(
        task_rep=task_rep,
        user_rep=user_rep,
        http_client=http_client,
    )

TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]

def get_user_service(user_rep: UserRepDep) -> UserService:
    return UserService(user_rep=user_rep)

UserServiceDep = Annotated[UserService, Depends(get_user_service)]