from src.models.orders import OrderORM
from src.schemas.order_schemas import OrderRequestSchema


def to_order_orm(order: OrderRequestSchema) -> OrderORM:
    data = order.model_dump()
    return OrderORM(
        is_deleted=False,
        **data,
    )


def to_orders_orm(orders: list[OrderRequestSchema]) -> list[OrderORM]:
    return [to_order_orm(order) for order in orders]
