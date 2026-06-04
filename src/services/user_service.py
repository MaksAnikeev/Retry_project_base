import logging
import uuid

from asyncpg import UniqueViolationError
from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError

from src.exceptions import (EmptyPasswordException, ObjectNotFoundException, UserAlreadyExistsException)
from src.repositories.user_rep import UsersRepository
from src.schemas.users_schemas import (
    UserRequestSchemas,
    UserCreateSchemas, UserGetSchemas,
)

class UserService:
    password_hash = PasswordHash.recommended()

    def __init__(
        self,
        user_rep: UsersRepository,
    ) -> None:
        self.user_rep = user_rep

    def verify_password(self, plain_password, hashed_password):
        return self.password_hash.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        return self.password_hash.hash(password)

    async def check_user_exists(self, user_id: uuid.UUID) -> None:
        user = await self.user_rep.one_or_none(id=user_id)
        if not user:
            logging.warning(f"User with id {user_id} not found")
            raise ObjectNotFoundException

    async def add_user(self, user_info: UserRequestSchemas) -> UserGetSchemas | None:
        if not user_info.password:
            logging.warning("Password cannot be empty")
            raise EmptyPasswordException
        hashed_password = self.get_password_hash(user_info.password)
        new_user_info = UserCreateSchemas(
            id=uuid.uuid4(),
            email=user_info.email,
            username=user_info.username,
            hashed_password=hashed_password,
        )

        try:
            new_user = await self.user_rep.add(new_user_info)
            await self.user_rep.commit()
            return new_user

        except IntegrityError as ex:
            await self.user_rep.rollback()

            if isinstance(ex.orig.__cause__, UniqueViolationError):
                logging.error(f"Unique violation for user '{user_info.email}'")
                raise UserAlreadyExistsException()
            else:
                logging.error(f"Unknown integrity error: {ex}")
                raise

        except Exception as e:
            await self.user_rep.rollback()
            logging.error(f"{user_info.email} \n {str(e)}")
            raise


    async def get_all(self) -> list[UserGetSchemas]:
        users = await self.user_rep.get_all()
        return users

    async def get_one_or_none(self, user_id: uuid.UUID) -> UserGetSchemas:
        await self.check_user_exists(user_id=user_id)
        user = await self.user_rep.one_or_none(id=user_id)
        return user

    async def delete(self, user_id: uuid.UUID) -> UserGetSchemas:
        await self.check_user_exists(user_id=user_id)
        user = await self.user_rep.delete(id=user_id)
        await self.user_rep.commit()
        return user