from src.models.base import Base
from src.models.users import UserORM
from src.models.tasks import TaskORM


all = [
    Base,
    UserORM,
    TaskORM,
]