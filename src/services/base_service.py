from src.exceptions import ObjectNotFoundException, UserNotFoundException, TaskNotFoundException
from src.utils.db_manager import DBManager


class BaseService:
    db: DBManager | None

    def __init__(self, db: DBManager | None = None) -> None:
        self.db = db

    async def check_user_exists(self, user_id: int) -> bool:
        try:
            await self.db.users.get_one(id=user_id)
        except ObjectNotFoundException:
            raise UserNotFoundException

    async def check_task_exists(self, task_id: int) -> bool:
        try:
            await self.db.tasks.get_one(id=task_id)
        except ObjectNotFoundException:
            raise TaskNotFoundException

    async def check_user_or_task_exists(
        self, user_id: int = None, task_id: int = None
    ) -> bool:
        if user_id and task_id:
            await self.check_user_exists(user_id)
            await self.check_task_exists(task_id)
            return True
        elif user_id:
            await self.check_user_exists(user_id)
            return True
        elif task_id:
            await self.check_task_exists(task_id)
            return True
        else:
            return False