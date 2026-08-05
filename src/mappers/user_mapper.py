from pwdlib import PasswordHash

from src.models import UserORM, TaskORM
from src.schemas.users_schemas import UserRequestSchema, UserUpdateWithTasksSchema


def to_user_orm(user_data: UserRequestSchema) -> UserORM:
    data = user_data.model_dump(exclude={"password", "tasks"})
    data["hashed_password"] = PasswordHash.recommended().hash(user_data.password)
    return UserORM(**data)


def update_user_fields(
    update_data: UserUpdateWithTasksSchema, user_orm: UserORM, password_hasher: PasswordHash
) -> None:
    update_dict = update_data.model_dump(
        exclude_unset=True,
        exclude={"password", "tasks"}
    )
    if update_data.password is not None:
        update_dict["hashed_password"] = password_hasher.hash(update_data.password)

    for field, value in update_dict.items():
        setattr(user_orm, field, value)
