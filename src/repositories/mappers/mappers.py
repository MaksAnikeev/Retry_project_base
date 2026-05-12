from src.models import TasksORM, UsersORM
from src.repositories.mappers.base_mapp import DataMapper
from src.schemas.tasks_schemas import TaskGetSchemas
from src.schemas.users_schemas import UserGetSchemas

class UserDataMapper(DataMapper):
    db_model = UsersORM
    schemas = UserGetSchemas

class TaskDataMapper(DataMapper):
    db_model = TasksORM
    schemas = TaskGetSchemas
