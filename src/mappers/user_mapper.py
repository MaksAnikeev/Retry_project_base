from pwdlib import PasswordHash

from src.models import UserORM, TaskORM
from src.schemas.users_schemas import UserRequestSchema


def to_user_orm(user: UserRequestSchema , tasks: list[TaskORM]) -> UserORM:
    return UserORM(
            username=user.username,
            email=user.email,
            hashed_password=PasswordHash.recommended().hash(user.password),
            is_active=True,
            is_deleted=False,
            tasks=tasks,
        )
