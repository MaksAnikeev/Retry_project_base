import logging

from aiohttp import ClientConnectorError, ServerDisconnectedError, ClientConnectionError, ClientOSError
from asyncio import TimeoutError as AsyncTimeoutError
from tenacity import retry, stop_after_attempt, retry_if_exception_type, wait_exponential_jitter

from src.exceptions import ExternalServiceUnavailableException

logger = logging.getLogger(__name__)


NETWORK_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    AsyncTimeoutError,
    ClientConnectorError,
    ClientConnectionError,
    ServerDisconnectedError,
    ClientOSError,
    ExternalServiceUnavailableException,
)

retry_standard = retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential_jitter(initial=2, max=60, exp_base=2, jitter=0.25),
    retry=retry_if_exception_type(NETWORK_EXCEPTIONS),
    reraise=True,
    before_sleep=lambda rs: logger.warning(
        f"🔁 RETRY {rs.attempt_number}/5 | "
        f"wait={rs.idle_for:.1f}s | "
        f"error={type(rs.outcome.exception()).__name__}"
    ),
)

retry_fast = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=1, max=30, exp_base=2, jitter=0.25),
    retry=retry_if_exception_type(NETWORK_EXCEPTIONS),
    reraise=True,
    before_sleep=lambda rs: logger.warning(
        f"🔁 FAST_RETRY {rs.attempt_number}/3 | "
        f"wait={rs.idle_for:.1f}s | "
        f"error={type(rs.outcome.exception()).__name__}"
    ),
)