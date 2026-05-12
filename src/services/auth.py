from datetime import datetime, timedelta, timezone

from pwdlib import PasswordHash
import jwt

from src.config import settings
from src.exceptions import (
    IncorrectPasswordException,
    WrongAccessToken,
    TimeoutAccessToken,
    EmptyAttributesException,
)
from src.schemas.users_schemas import (
    UserRequestSchemas,
    UserCreateSchemas,
)
from src.services.base_service import BaseService


class AuthService(BaseService):
    password_hash = PasswordHash.recommended()

    def create_access_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt

    def verify_password(self, plain_password, hashed_password):
        return self.password_hash.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        return self.password_hash.hash(password)

    def get_data_from_hash(self, token):
        try:
            data = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
            return data
        except jwt.ExpiredSignatureError:
            raise TimeoutAccessToken
        except jwt.exceptions.DecodeError:
            raise WrongAccessToken

    async def add_user(self, user_info: UserRequestSchemas):
        if not user_info.password:
            raise EmptyAttributesException
        hashed_password = self.get_password_hash(user_info.password)
        new_user_info = UserCreateSchemas(
            email=user_info.email,
            username=user_info.username,
            hashed_password=hashed_password,
        )
        new_user = await self.db.users.add(new_user_info)
        return new_user

    async def get_user_with_hashed_password(self, user_info: UserRequestSchemas):
        user = await self.db.users.get_user_with_hashed_password(email=user_info.email)

        if not self.verify_password(user_info.password, user.hashed_password):
            raise IncorrectPasswordException
        access_token = self.create_access_token({"user_id": user.id})

        return access_token

