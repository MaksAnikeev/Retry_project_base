from src.models import OrderORM
from src.repositories.base import BaseRepository
from src.schemas.order_schemas import OrderGetSchema


class OrderRepository(BaseRepository[OrderORM, OrderGetSchema]):
    model = OrderORM
