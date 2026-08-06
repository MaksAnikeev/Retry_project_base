from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_session
from src.database.unit_of_work import UnitOfWork
from src.dependencies.dependencies_tasks import UserRepDep
from src.services.order_service import OrderService
from src.services.user_service import UserService

SessionDep = Annotated[AsyncSession, Depends(get_session)]

def get_uow(session: SessionDep) -> UnitOfWork:
    return UnitOfWork(session=session)

UowDep = Annotated[UnitOfWork, Depends(get_uow)]

def get_user_service(
    user_rep: UserRepDep,
) -> UserService:
    return UserService(user_rep=user_rep)

UserServiceDep = Annotated[UserService, Depends(get_user_service)]

def get_order_service(
    uow: UowDep,
    user_service: UserServiceDep
) -> OrderService:
    return OrderService(
        uow=uow,
        user_service=user_service
    )

OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]
