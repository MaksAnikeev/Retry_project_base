from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_session
from src.database.unit_of_work import UnitOfWork
from src.repositories.order_rep import OrderRepository
from src.repositories.outbox_rep import OutboxRepository
from src.services.order_service import OrderService
from src.services.outbox_service import OutboxService

SessionDep = Annotated[AsyncSession, Depends(get_session)]

def get_uow(session: SessionDep) -> UnitOfWork:
    return UnitOfWork(session=session)

UowDep = Annotated[UnitOfWork, Depends(get_uow)]

def get_order_rep(session: SessionDep) -> OrderRepository:
    return OrderRepository(session=session)

OrderRepDep = Annotated[OrderRepository, Depends(get_order_rep)]

def get_outbox_rep(session: SessionDep) -> OutboxRepository:
    return OutboxRepository(session=session)

OutboxRepDep = Annotated[OutboxRepository, Depends(get_outbox_rep)]

def get_outbox_service(
    outbox_repo: OutboxRepDep,
) -> OutboxService:
    return OutboxService(
        outbox_repo=outbox_repo,
    )

OutboxServiceDep = Annotated[OutboxService, Depends(get_outbox_service)]

def get_order_service(
    uow: UowDep,
    order_repo: OrderRepDep,
    outbox_service: OutboxServiceDep,
) -> OrderService:
    return OrderService(
        uow=uow,
        order_repo=order_repo,
        outbox_service=outbox_service,
    )

OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]
