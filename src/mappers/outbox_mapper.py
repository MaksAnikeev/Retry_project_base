from collections.abc import Iterable

from src.config import settings
from src.models.orders import OrderORM
from src.models.outbox import OutboxORM
from src.schemas.outbox_schemas import OutboxStatus


def to_order_created_outbox(order: OrderORM) -> OutboxORM:
    payload = {
            "id": str(order.id),
            "user_id": str(order.user_id),
            "product_name": order.product_name,
            "description": order.description,
            "price": order.price,
            "quantity": order.quantity,
    }

    return OutboxORM(
        topic=settings.ORDER_TOPIC,
        aggregate_type=settings.ORDER_AGGREGATE_TYPE,
        event_type=settings.ORDER_EVENT_TYPE,
        payload=payload,
        status=OutboxStatus.PENDING.value,
    )


def to_order_created_outboxes(
    orders: Iterable[OrderORM],
) -> list[OutboxORM]:
    return [to_order_created_outbox(order) for order in orders]
