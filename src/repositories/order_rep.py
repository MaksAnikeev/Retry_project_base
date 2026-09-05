from src.models import OrderORM
from src.repositories.base import BaseRepository


class OrderRepository(BaseRepository[OrderORM]):
    model = OrderORM
