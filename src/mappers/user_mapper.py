from pwdlib import PasswordHash

from src.models import UserORM
from src.schemas.users_schemas import UserRequestSchema, UserUpdateWithTasksSchema


def to_user_orm(user_data: UserRequestSchema) -> UserORM:
    data = user_data.model_dump(exclude={"password", "tasks"})
    data["hashed_password"] = PasswordHash.recommended().hash(user_data.password)
    data["is_active"] = True
    data["is_deleted"] = False
    return UserORM(**data)


def update_user_fields(
    update_data: UserUpdateWithTasksSchema, user_orm: UserORM, password_hasher: PasswordHash
) -> None:
    if update_data.username is not None:
        user_orm.username = update_data.username

    if update_data.email is not None:
        user_orm.email = str(update_data.email)

    if update_data.is_active is not None:
        user_orm.is_active = update_data.is_active

    if update_data.is_deleted is not None:
        user_orm.is_deleted = update_data.is_deleted

    if update_data.password is not None:
        user_orm.hashed_password = password_hasher.hash(update_data.password)
