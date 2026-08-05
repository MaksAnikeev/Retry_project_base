from abc import ABC, abstractmethod
from http import HTTPStatus
from typing import Any

import aiohttp


class BaseHTTPClient(ABC):

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
        raise exception

    @abstractmethod
    def _create_exception(
        self,
        status: int,
        error_text: str,
        url: str,
    ) -> Exception: ...
