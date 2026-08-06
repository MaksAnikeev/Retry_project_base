import logging
import uuid

from src.exceptions import ObjectNotFoundException
from src.repositories.user_rep import UsersRepository


class UserService:

    def __init__(
        self,
        user_rep: UsersRepository,
    ) -> None:
        self.user_rep = user_rep

        self.logger = logging.getLogger(self.__class__.__name__)

    async def validate_users_ids(
        self,
        user_ids: set[uuid.UUID],
    ) -> None:
        existing_user_ids = await self.user_rep.get_existing_user_ids(user_ids)
        missing_user_ids = user_ids - existing_user_ids

        if missing_user_ids:
            self.logger.warning(
                "Attempt to create orders for non-existent users",
                extra={"missing_user_ids": missing_user_ids},
            )
            raise ObjectNotFoundException(
                detail=f"Пользователи не найдены: {missing_user_ids}"
            )
