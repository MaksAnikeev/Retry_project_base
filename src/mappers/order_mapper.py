from typing import Any

from src.models.orders import OrderORM
from src.schemas.order_schemas import OrderRequestSchema, OrderGetSchema, OrderOutboxSchema


def to_order_orm(order: OrderRequestSchema) -> OrderORM:
    data = order.model_dump()
    return OrderORM(
        is_deleted=False,
        **data,
    )


def to_orders_orm(orders: list[OrderRequestSchema]) -> list[OrderORM]:
    return [to_order_orm(order) for order in orders]


def to_order_schema(order_orm: OrderORM) -> OrderGetSchema:
    return OrderGetSchema.model_validate(order_orm, from_attributes=True)


def to_orders_schema(orders_orm: list[OrderORM]) -> list[OrderGetSchema]:
    return [to_order_schema(order_orm) for order_orm in orders_orm]


def to_order_outbox_schema(payload: dict[str, Any]) -> OrderOutboxSchema:
    return OrderOutboxSchema.model_validate(payload)
