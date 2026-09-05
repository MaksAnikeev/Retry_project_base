from typing import Annotated

from fastapi import Depends

from src.dependencies.dependencies_outbox import OutboxServiceDep

from src.database.db import SessionDep
from src.dependencies.dependencies_uow import UowDep
from src.repositories.order_rep import OrderRepository
from src.services.order_service import OrderService


def get_order_rep(session: SessionDep) -> OrderRepository:
    return OrderRepository(session=session)

OrderRepDep = Annotated[OrderRepository, Depends(get_order_rep)]

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
