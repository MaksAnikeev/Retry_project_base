import aiohttp
from typing import Optional

from aiohttp import ClientError

from src.clients.base_http_client import BaseHTTPClient
from src.config import settings
from src.utils.retry_client import retry_standard

from src.utils.circuit_breaker import circuit_breaker_standard
from src.exceptions import ExternalServiceUnavailableException
from src.schemas.tasks_schemas import TaskAPIRequestSchema, TaskAPIResponseSchema


class ReportServiceClient(BaseHTTPClient):

    def __init__(
            self,
            base_url: str = settings.REPORT_SERVICE_URL,
            timeout: int = settings.REPORT_SERVICE_TIMEOUT,
    ):
        super().__init__()
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

    @circuit_breaker_standard
    @retry_standard
    async def get_reports_batch(
        self,
        tasks: list[TaskAPIRequestSchema],
    ) -> list[TaskAPIResponseSchema]:
        if not tasks:
            return []
        session = await self.get_session()
        url = f"{self.base_url}/reports"
        payload = [task.model_dump(mode="json") for task in tasks]

        try:
            async with session.post(url, json=payload) as response:
                response_data = await self._handle_response(response, url)
                return [TaskAPIResponseSchema(**item) for item in response_data]

        except (ClientError, TimeoutError) as e:
            self.logger.error(
                "Network error calling external service",
                extra={"url": url, "error": str(e), "error_type": type(e).__name__},
            )
            raise ExternalServiceUnavailableException(
                detail=f"Network error: {type(e).__name__}"
            ) from e


def create_report_client() -> "ReportServiceClient":
    return ReportServiceClient(
        base_url=settings.REPORT_SERVICE_URL,
        timeout=settings.REPORT_SERVICE_TIMEOUT,
    )