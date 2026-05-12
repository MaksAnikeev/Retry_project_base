from pydantic import EmailStr
from sqlalchemy import select, func

from src.exceptions import ObjectNotFoundException
from src.models.users import UsersORM
from src.repositories.base import BaseRepository
from src.repositories.mappers.mappers import UserDataMapper
from src.schemas.users_schemas import UserGetHashedPassword


class UsersRepository(BaseRepository):
    model = UsersORM
    mapper = UserDataMapper

    async def get_user_with_hashed_password(self, email: EmailStr):
        query = select(self.model).filter_by(email=email)
        query_result = await self.session.execute(query)
        result = query_result.scalars().one_or_none()
        if not result:
            raise ObjectNotFoundException
        return UserGetHashedPassword.model_validate(result, from_attributes=True)
