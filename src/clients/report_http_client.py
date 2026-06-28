import logging

import aiohttp
from typing import Optional

from aiohttp import ClientError, ClientTimeout

from src.config import get_settings
from src.exceptions.infra import ExternalServiceClientException
from src.utils.retry_client import retry_standard

from src.utils.circuit_breaker import circuit_breaker_standard
from src.exceptions import ExternalServiceUnavailableException, ObjectNotFoundException
from src.schemas.tasks_schemas import TaskAPIRequestSchema, TaskAPIResponseSchema

settings = get_settings()


class ReportServiceClient:

    def __init__(
            self,
            base_url: str = settings.REPORT_SERVICE_URL,
            timeout: int = settings.REPORT_SERVICE_TIMEOUT,
    ):
        self.base_url = base_url.rstrip("/")
        self._default_timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None

        self.logger = logging.getLogger(self.__class__.__name__)

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
                if response.status >= 500:
                    raise ExternalServiceUnavailableException(
                        detail=f"External service error: {response.status}"
                    )

                elif response.status == 429:
                    raise ExternalServiceUnavailableException(
                        detail="Rate limit exceeded"
                    )

                elif response.status == 404:
                    self.logger.warning(
                        "Resource not found",
                        extra={"url": url, "status": response.status},
                    )
                    raise ObjectNotFoundException(
                        detail="Reports endpoint not found"
                    )

                elif 400 <= response.status < 500:
                    error_text = await response.text()
                    self.logger.error(
                        "Client error from external service",
                        extra={
                            "url": url,
                            "status": response.status,
                            "error": error_text[:200],
                        },
                    )
                    raise ExternalServiceClientException(
                        detail=f"Invalid request: {error_text[:200]}"
                    )

                return [TaskAPIResponseSchema(**item) for item in await response.json()]

        except (ClientError, TimeoutError) as e:
            self.logger.error(
                "Network error calling external service",
                extra={"url": url, "error": str(e), "error_type": type(e).__name__},
            )
            raise ExternalServiceUnavailableException(
                detail=f"Network error: {type(e).__name__}"
            ) from e


def create_report_client() -> "ReportServiceClient":
    settings = get_settings()
    return ReportServiceClient(
        base_url=settings.REPORT_SERVICE_URL,
        timeout=settings.REPORT_SERVICE_TIMEOUT,
    )