import aiohttp
from typing import Optional
from src.config import settings
from src.exceptions.exceptions import TaskServiceErrorHTTPException
from src.schemas.tasks_schemas import TaskAPIRequestSchemas, TaskAPIResponseSchemas


class TaskServiceClient:
    """HTTP клиент для внешних вызовов (если сервисов несколько)"""

    def __init__(
            self,
            base_url: str | None = None,
            timeout: int = 30,
    ):
        self.base_url = (base_url or settings.TASK_SERVICE_URL).rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        """Ленивое создание сессии (singleton)"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session

    # Вход в контекст: гарантируем, что сессия создана
    async def __aenter__(self) -> "TaskServiceClient":
        await self.get_session()
        return self

    # Выход из контекста: закрываем сессию
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session and not self._session.closed:
            await self._session.close()
        return False

    async def get_report(self, task_info: TaskAPIRequestSchemas) -> TaskAPIResponseSchemas:
        session = await self.get_session()
        url = f"{self.base_url}/reports"

        async with session.post(url, json=task_info.model_dump(mode='json')) as response:
            if not response.ok:
                raise TaskServiceErrorHTTPException()
            return TaskAPIResponseSchemas(**await response.json())

