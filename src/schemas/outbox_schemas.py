from enum import Enum


class OutboxStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class OrderEventType(str, Enum):
    ORDER_CREATED = "OrderCreated"
    ORDER_PAID = "OrderPaid"
    ORDER_SHIPPED = "OrderShipped"
    ORDER_CANCELLED = "OrderCancelled"


class OrderAggregateType(str, Enum):
    ORDER = "Order"