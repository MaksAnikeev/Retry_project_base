from src.models.users import UsersORM
from src.repositories.base import BaseRepository
from src.schemas.users_schemas import UserGetSchemas


class UsersRepository(BaseRepository):
    model = UsersORM
    schemas = UserGetSchemas
