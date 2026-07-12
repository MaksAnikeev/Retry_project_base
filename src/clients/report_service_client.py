import asyncio
import aiohttp
from http import HTTPStatus
from typing import Optional

import circuitbreaker

from src.clients.base_http_client import BaseHTTPClient
from src.config import settings
from src.exceptions.external_service import ExternalServiceClientException
from src.utils.retry_client import retry_standard

from src.utils.circuit_breaker import circuit_breaker_standard
from src.exceptions import ExternalServiceUnavailableException, ObjectNotFoundException
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

        self._error_mapping: dict[int, Exception] = {
            HTTPStatus.TOO_MANY_REQUESTS: ExternalServiceUnavailableException(
                detail="Rate limit exceeded"
            ),
            HTTPStatus.NOT_FOUND: ObjectNotFoundException(
                detail="Reports endpoint not found"
            ),
            HTTPStatus.BAD_GATEWAY: ExternalServiceUnavailableException(
                detail="Bad gateway"
            ),
            HTTPStatus.SERVICE_UNAVAILABLE: ExternalServiceUnavailableException(
                detail="Service unavailable"
            ),
            HTTPStatus.GATEWAY_TIMEOUT: ExternalServiceUnavailableException(
                detail="Gateway timeout"
            ),
        }

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

        error = self._error_mapping.get(status)
        if error is not None:
            return error
        if status >= HTTPStatus.INTERNAL_SERVER_ERROR:
            return ExternalServiceUnavailableException(
                detail=f"External service error: {status}"
            )
        return ExternalServiceClientException(
            detail=f"Invalid request: {error_text[:200]}"
        )

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

        except circuitbreaker.CircuitBreakerError:
            raise ExternalServiceUnavailableException(
                detail="Service temporarily unavailable (circuit breaker open)"
            )

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            self.logger.warning(
                "Network error calling external service",
                extra={"url": url, "error_type": type(e).__name__},
                exc_info=False,
            )
            raise ExternalServiceUnavailableException(
                detail=f"Network error: {type(e).__name__}"
            )


def create_report_client() -> "ReportServiceClient":
    return ReportServiceClient(
        base_url=settings.REPORT_SERVICE_URL,
        timeout=settings.REPORT_SERVICE_TIMEOUT,
    )