from fastapi import APIRouter, Body

from src.dependencies.dependencies_orders import OrderServiceDep
from src.schemas.order_schemas import OrderGetSchema, OrderRequestSchema, example_add_orders

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", summary="создание заказа")
async def create_orders(
    service: OrderServiceDep,
    order_data: list[OrderRequestSchema] = Body(openapi_examples=example_add_orders),
) -> list[OrderGetSchema]:
    return await service.create_orders(order_data)
