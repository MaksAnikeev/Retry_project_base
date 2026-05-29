from typing import Annotated
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import async_session_factory
from src.repositories.task_rep import TasksRepository
from src.repositories.user_rep import UsersRepository
from src.services.task_service import TaskService
from src.services.user_service import UserService
from src.clients.http_client import TaskServiceClient
from src.utils.circuit_breaker import CircuitBreaker

# Глобальный HTTP клиент (заполняется в lifespan)
_task_client: TaskServiceClient | None = None
_task_service_cb: CircuitBreaker | None = None

def get_task_client() -> TaskServiceClient:
    """Dependency для получения HTTP клиента"""
    if _task_client is None:
        raise HTTPException(
            status_code=503,
            detail="Task Service Client not initialized",
        )
    return _task_client

TaskClientDep = Annotated[TaskServiceClient, Depends(get_task_client)]

def get_circuit_breaker() -> CircuitBreaker:
    if _task_service_cb is None:
        raise HTTPException(503, detail="CircuitBreaker not initialized")
    return _task_service_cb

CircuitBreakerDep = Annotated[CircuitBreaker, Depends(get_circuit_breaker)]


async def get_session() -> AsyncGenerator[AsyncSession]:
    async with async_session_factory() as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_task_rep(session: SessionDep) -> TasksRepository:
    return TasksRepository(session=session)

TaskRepDep = Annotated[TasksRepository, Depends(get_task_rep)]


def get_user_rep(session: SessionDep) -> UsersRepository:
    return UsersRepository(session=session)

UserRepDep = Annotated[UsersRepository, Depends(get_user_rep)]


def get_task_service(
    task_rep: TaskRepDep,
    user_rep: UserRepDep,
    http_client: TaskClientDep,
    circuit_breaker: CircuitBreakerDep
) -> TaskService:
    return TaskService(
        task_rep=task_rep,
        user_rep=user_rep,
        http_client=http_client,
        circuit_breaker=circuit_breaker
    )

TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]


def get_user_service(user_rep: UserRepDep) -> UserService:
    return UserService(user_rep=user_rep)

UserServiceDep = Annotated[UserService, Depends(get_user_service)]