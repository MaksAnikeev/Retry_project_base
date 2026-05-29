from src.models.base import Base
from src.models.users import UsersORM
from src.models.tasks import TasksORM


all = [
    Base,
    UsersORM,
    TasksORM,
]