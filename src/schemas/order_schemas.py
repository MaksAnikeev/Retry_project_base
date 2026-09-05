import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from src.schemas.kafka_schemas import BaseKafkaMessageSchema, BaseKafkaHeadersSchema


class OrderEventType(str, Enum):
    ORDER_CREATED = "OrderCreated"
    ORDER_PAID = "OrderPaid"
    ORDER_SHIPPED = "OrderShipped"
    ORDER_CANCELLED = "OrderCancelled"


class OrderAggregateType(str, Enum):
    ORDER = "Order"


class OrderBase(BaseModel):
    user_id: uuid.UUID = Field(..., description="Ид пользователя, создавшего заказ")
    product_name: str = Field(
        ...,
        max_length=100,
        description="Название продукта",
    )
    description: str | None = Field(
        None,
        description="Описание продукта"
    )
    price: int = Field(
        ...,
        ge=0,
        description="Цена продукта",
    )
    quantity: int = Field(
        ...,
        gt=0,
        description="Количество единиц продукта",
    )

class OrderRequestSchema(OrderBase):
    ...

example_add_orders = {
    "1": {
        "summary": "Велик",
        "value": [
                {
                    "user_id": "c54e6396-d7d2-4d53-bece-51c91990fa5b",
                    "product_name": "Велосипед",
                    "description": "Крутой горный велик",
                    "price": 6500000,
                    "quantity": 1,
                },
                {
                    "user_id": "c54e6396-d7d2-4d53-bece-51c91990fa5b",
                    "product_name": "Колесо для велосипеда",
                    "price": 500000,
                    "quantity": 3,
                },
                {
                    "user_id": "de662447-4321-4922-9f88-16150f295c99",
                    "product_name": "Удочка",
                    "price": 1500000,
                    "quantity": 2,
                },
            ]
    },
    "2": {
        "summary": "Ошибка",
        "value": [
                {
                    "user_id": "c54e6396-d7d2-4d53-bece-51c91990fa5b",
                    "price": 1500000,
                    "quantity": 2,
                },
            ],
    },
}

class OrderGetSchema(OrderBase):
    id: uuid.UUID
    is_deleted: bool = Field(..., description="Пользователь удален")
    created_at: datetime = Field(..., description="Дата регистрации пользователя")
    updated_at: datetime | None = Field(None, description="Дата обновления информации о пользователе")


class OrderOutboxSchema(OrderBase):
    id: uuid.UUID


class OrderHeadersSchema(BaseKafkaHeadersSchema):
    event_type: str
    aggregate_type: str = "Order"
    event_id: str | None = None
    correlation_id: str | None = None
    content_type: str = "application/json"


class OrderCreateMessageSchema(BaseKafkaMessageSchema):
    payload: OrderOutboxSchema
    headers: OrderHeadersSchema

