import logging
from abc import ABC, abstractmethod
from http import HTTPStatus
from typing import Any

import aiohttp


class BaseHTTPClient(ABC):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    async def _handle_response(
        self,
        response: aiohttp.ClientResponse,
        url: str,
    ) -> Any:

        status = response.status
        if status < HTTPStatus.BAD_REQUEST:
            return await response.json()

        error_text = await response.text()
        exception = self._create_exception(status, error_text, url)

        if status >= HTTPStatus.INTERNAL_SERVER_ERROR:
            self.logger.warning(
                "Server error from external service",
                extra={"url": url, "status": status, "error": error_text[:200]},
            )
        else:
            self.logger.warning(
                "Client error from external service",
                extra={"url": url, "status": status, "error": error_text[:200]},
            )

        raise exception

    @abstractmethod
    def _create_exception(
        self,
        status: int,
        error_text: str,
        url: str,
    ) -> Exception: ...
