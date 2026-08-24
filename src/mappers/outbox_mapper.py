from collections.abc import Iterable

from src.config import settings
from src.models.orders import OrderORM
from src.models.outbox import OutboxORM
from src.schemas.order_schemas import OrderOutboxSchema
from src.schemas.outbox_schemas import OutboxStatus, OrderAggregateType, OrderEventType


def to_order_created_outbox(order: OrderORM) -> OutboxORM:
    payload_schema = OrderOutboxSchema.model_validate(order, from_attributes=True)
    payload = payload_schema.model_dump(mode="json")

    return OutboxORM(
        topic=settings.ORDER_TOPIC,
        aggregate_type=OrderAggregateType.ORDER.value,
        aggregate_id=order.id,
        event_type=OrderEventType.ORDER_CREATED.value,
        payload=payload,
        status=OutboxStatus.PENDING,
    )


def to_order_created_outboxes(
    orders: Iterable[OrderORM],
) -> list[OutboxORM]:
    return [to_order_created_outbox(order) for order in orders]
