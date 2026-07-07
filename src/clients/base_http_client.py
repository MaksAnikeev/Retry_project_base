import logging
from http import HTTPStatus

import aiohttp

from src.exceptions import ExternalServiceUnavailableException, ObjectNotFoundException
from src.exceptions.external_service import ExternalServiceClientException


class BaseHTTPClient:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

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

    async def _handle_response(
        self,
        response: aiohttp.ClientResponse,
        url: str,
    ) -> any:
        status = response.status
        if status < HTTPStatus.BAD_REQUEST:
            return await response.json()

        error = self._error_mapping.get(status)
        if error is not None:
            self.logger.warning(
                "HTTP error from external service",
                extra={"url": url, "status": status, "error": str(error.detail)},
            )
            raise error

        error_text = await response.text()

        if status >= HTTPStatus.INTERNAL_SERVER_ERROR:
            self.logger.warning(
                "Server error from external service",
                extra={"url": url, "status": status, "error": error_text[:200]},
            )
            raise ExternalServiceUnavailableException(
                detail=f"External service error: {status}"
            )
        self.logger.error(
            "Client error from external service",
            extra={"url": url, "status": status, "error": error_text[:200]},
        )
        raise ExternalServiceClientException(
            detail=f"Invalid request: {error_text[:200]}"
        )
