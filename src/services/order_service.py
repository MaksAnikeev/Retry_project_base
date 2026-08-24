import logging

from src.database.unit_of_work import UnitOfWork
from src.mappers.order_mapper import to_orders_orm
from src.mappers.outbox_mapper import to_order_created_outboxes
from src.repositories.order_rep import OrderRepository
from src.schemas.order_schemas import OrderGetSchema, OrderRequestSchema
from src.services.outbox_service import OutboxService


class OrderService:

    def __init__(
        self,
        uow: UnitOfWork,
        order_repo: OrderRepository,
        outbox_service: OutboxService,
    ) -> None:
        self.uow = uow
        self.order_repo = order_repo
        self.outbox_service = outbox_service

        self.logger = logging.getLogger(self.__class__.__name__)

    async def create_orders(
        self,
        orders_data: list[OrderRequestSchema],
    ) -> list[OrderGetSchema]:
        orders_orm = to_orders_orm(orders_data)
        async with self.uow:
            orders_orm = await self.order_repo.add_many(orders_orm)
            outboxes_orm = to_order_created_outboxes(orders_orm)
            await self.outbox_service.publish_events(outboxes_orm)
        return [OrderGetSchema.model_validate(order_orm, from_attributes=True) for order_orm in orders_orm]
