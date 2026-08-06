from src.models.base import Base
from src.models.orders import OrderORM
from src.models.outbox import OutboxORM
from src.models.users import UserORM
from src.models.tasks import TaskORM


all = [
    Base,
    UserORM,
    TaskORM,
    OrderORM,
    OutboxORM,
]