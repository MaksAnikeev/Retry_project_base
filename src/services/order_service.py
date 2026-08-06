import logging

from src.database.unit_of_work import UnitOfWork
from src.mappers.order_mapper import to_orders_orm
from src.mappers.outbox_mapper import to_order_created_outboxes
from src.schemas.order_schemas import OrderGetSchema, OrderRequestSchema
from src.services.user_service import UserService


class OrderService:

    def __init__(
        self,
        uow: UnitOfWork,
        user_service: UserService
    ) -> None:
        self.uow = uow
        self.user_service = user_service

        self.logger = logging.getLogger(self.__class__.__name__)

    async def create_orders(
        self,
        orders_data: list[OrderRequestSchema],
    ) -> list[OrderGetSchema]:
        user_ids = {order.user_id for order in orders_data}
        async with self.uow:
            await self.user_service.validate_users_ids(user_ids)

            orders_orm = to_orders_orm(orders_data)
            self.uow.session.add_all(orders_orm)
            await self.uow.session.flush()
            for order in orders_orm:
                await self.uow.session.refresh(order)

            outboxes_orm = to_order_created_outboxes(orders_orm)
            self.uow.session.add_all(outboxes_orm)
        return [OrderGetSchema.model_validate(order_orm, from_attributes=True) for order_orm in orders_orm]
