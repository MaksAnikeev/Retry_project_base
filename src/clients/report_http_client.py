import logging

import aiohttp
from typing import Optional

from aiohttp import ClientConnectorError, ClientConnectionError, ServerDisconnectedError, ClientOSError, ClientError, \
    ClientTimeout
from asyncio import TimeoutError as AsyncTimeoutError

from src.utils.retry_client import retry_standard

from src.utils.circuit_breaker import circuit_breaker_standard
from src.exceptions import ExternalServiceUnavailableException
from src.schemas.tasks_schemas import TaskAPIRequestSchemas, TaskAPIResponseSchemas


class ReportServiceClient:

    def __init__(
            self,
            base_url: str,
            timeout: int = 30,
    ):
        self.base_url = base_url.rstrip("/")
        self._default_timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self._default_timeout)
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def check_health(self, timeout: float = 3.0) -> bool:
        session = await self.get_session()
        try:
            request_timeout = ClientTimeout(total=timeout)
            async with session.get(
                f"{self.base_url}/health",
                timeout=request_timeout
            ) as response:
                return response.status == 200
        except Exception as ex:
            logging.error(
                f"Health check failed for external service: {self.base_url}/health. "
                f"Reason: {type(ex).__name__} - {ex}"
            )
            return False

    @circuit_breaker_standard
    @retry_standard
    async def get_report(self, task_info: TaskAPIRequestSchemas) -> TaskAPIResponseSchemas:
        session = await self.get_session()
        url = f"{self.base_url}/reports"

        try:
            async with session.post(url, json=task_info.model_dump(mode='json')) as response:
                if not response.ok:
                    error_text = await response.text()
                    raise ExternalServiceUnavailableException(
                        detail=f"External service returned {response.status}: {error_text[:100]}"
                    )
                return TaskAPIResponseSchemas(**await response.json())

        except (
                ClientConnectorError,
                ClientConnectionError,
                ServerDisconnectedError,
                ClientOSError,
                AsyncTimeoutError,
                TimeoutError,
                ClientError,
        ) as e:
            logging.error(
                f"Failed connect for external service: {self.base_url}/reports. "
                f"Reason: {type(e).__name__} - {e}"
            )
            raise ExternalServiceUnavailableException(
                detail=f"Failed to connect to task service: {type(e).__name__}"
            ) from e

