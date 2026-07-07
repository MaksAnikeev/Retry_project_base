import asyncio
import http
import logging

from aiohttp import ClientTimeout
from sqlalchemy import text

from src.clients.report_service_client import ReportServiceClient
from src.db import async_session_factory

logger = logging.getLogger(__name__)


class HealthDB:
    HEALTH_CHECK_TIMEOUT = 5.0

    @staticmethod
    async def check_database() -> bool:
        try:
            async with async_session_factory() as session:
                await asyncio.wait_for(
                    session.execute(text("SELECT 1")),
                    timeout=HealthDB.HEALTH_CHECK_TIMEOUT
                )
                return True
        except asyncio.TimeoutError:
            logging.error(f"Health check: Database connection TIMEOUT after {HealthDB.HEALTH_CHECK_TIMEOUT}s")
            return False
        except Exception as e:
            logging.error(f"Health check: Database connection failed - {type(e).__name__}: {e}")
            return False


async def check_health(
    client: ReportServiceClient,
    timeout: float = 3.0,
) -> bool:
    session = await client.get_session()
    try:
        request_timeout = ClientTimeout(total=timeout)
        async with session.get(
            f"{client.base_url}/health",
            timeout=request_timeout
        ) as response:
            return response.status == http.HTTPStatus.OK
    except Exception as ex:
        logger.error(
            "Health check failed for external service",
            extra={
                "url": client.base_url,
                "error": str(ex),
                "error_type": type(ex).__name__,
            },
        )
        return False