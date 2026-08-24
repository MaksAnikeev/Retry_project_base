from unittest.mock import Mock
from uuid import uuid4

from pwdlib import PasswordHash

from src.mappers.user_mapper import update_user_fields
from src.schemas.users_schemas import UserUpdateWithTasksSchema


def test_update_user_fields():
    user = Mock()
    user.id = uuid4()
    user.username = "old_username"
    user.email = "old@test.com"
    user.hashed_password = "old_hash"

    update_data = UserUpdateWithTasksSchema(
        id=user.id,
        password='new_password',
        username='new_username',
        tasks=[],
    )
    password_hash = PasswordHash.recommended()
    update_user_fields(update_data, user, password_hash)

    assert user.username == "new_username"
    assert password_hash.verify("new_password", user.hashed_password)


def test_update_user_fields_does_not_rewrite_null_fields():
    user = Mock()
    user.id = uuid4()
    user.username = "old_username"
    user.hashed_password = "old_hash"
    user.tasks = ["existing_task_1", "existing_task_2"]

    update_data = UserUpdateWithTasksSchema(
        id=user.id,
        username="new_username",
        tasks=[],
    )

    password_hash = PasswordHash.recommended()
    update_user_fields(update_data, user, password_hash)

    assert user.username == "new_username"
    assert user.hashed_password == "old_hash"
    assert user.tasks is not None


def test_produces_different_hashes_for_same_password():
    user1 = Mock()
    user1.id = uuid4()

    user2 = Mock()
    user2.id = uuid4()

    update_data = UserUpdateWithTasksSchema(
        id=uuid4(),
        password="same_password",
        tasks=[],
    )
    password_hash = PasswordHash.recommended()
    update_user_fields(update_data, user1, password_hash)
    update_user_fields(update_data, user2, password_hash)

    assert user1.hashed_password != user2.hashed_password
    assert password_hash.verify("same_password", user1.hashed_password)
    assert password_hash.verify("same_password", user2.hashed_password)
