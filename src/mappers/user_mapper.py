from pwdlib import PasswordHash

from src.schemas.users_schemas import UserRequestSchema


def schema_to_insert_dict(user_data: UserRequestSchema) -> dict:
    return {
        "username": user_data.username,
        "email": user_data.email,
        "hashed_password": PasswordHash.recommended().hash(user_data.password),
        "is_active": True,
        "is_deleted": False,
    }