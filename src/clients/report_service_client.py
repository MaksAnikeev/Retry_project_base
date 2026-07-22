from http import HTTPStatus

import aiohttp

from src.clients.base_http_client import BaseHTTPClient
from src.config import settings
from src.exceptions import (
    BaseDomainException,
    ExternalServiceUnavailableException,
    ObjectNotFoundException,
)
from src.exceptions.external_service import ExternalServiceClientException
from src.schemas.tasks_schemas import TaskAPIRequestSchema, TaskAPIResponseSchema
from src.utils.circuit_breaker import circuit_breaker_standard
from src.utils.retry_client import retry_standard


class ReportServiceClient(BaseHTTPClient):
    _ERROR_MAPPING: dict[int, type[BaseDomainException]] = {
        HTTPStatus.TOO_MANY_REQUESTS: ExternalServiceUnavailableException,
        HTTPStatus.NOT_FOUND: ObjectNotFoundException,
        HTTPStatus.BAD_GATEWAY: ExternalServiceUnavailableException,
        HTTPStatus.SERVICE_UNAVAILABLE: ExternalServiceUnavailableException,
        HTTPStatus.GATEWAY_TIMEOUT: ExternalServiceUnavailableException,
    }

    def __init__(
        self,
        base_url: str = settings.REPORT_SERVICE_URL,
        timeout: int = settings.REPORT_SERVICE_TIMEOUT,
    ):
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self._default_timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: aiohttp.ClientSession | None = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self._default_timeout)
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    def _create_exception(
        self,
        status: int,
        error_text: str,
        url: str,
    ) -> Exception:

        exception_class = self._ERROR_MAPPING.get(status)

        if exception_class is not None:
            return exception_class(detail=f"HTTP {status}: {error_text[:200]}")

        if status >= HTTPStatus.INTERNAL_SERVER_ERROR:
            return ExternalServiceUnavailableException(detail=f"External service error: {status}")

        return ExternalServiceClientException(detail=f"Invalid request: {error_text[:200]}")

    @circuit_breaker_standard
    @retry_standard
    async def get_reports_batch(
        self,
        tasks: list[TaskAPIRequestSchema],
    ) -> list[TaskAPIResponseSchema]:

        session = await self.get_session()
        url = f"{self.base_url}/reports"
        payload = [task.model_dump(mode="json") for task in tasks]

        try:
            async with session.post(url, json=payload) as response:
                response_data = await self._handle_response(response, url)
                return [TaskAPIResponseSchema(**item) for item in response_data]

        except (TimeoutError, aiohttp.ClientError) as e:
            raise ExternalServiceUnavailableException(detail=f"Network error: {type(e).__name__}")


def create_report_client() -> "ReportServiceClient":
    return ReportServiceClient(
        base_url=settings.REPORT_SERVICE_URL,
        timeout=settings.REPORT_SERVICE_TIMEOUT,
    )
