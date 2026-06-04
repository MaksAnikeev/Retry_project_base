import logging
from aiohttp import ClientConnectorError, ServerDisconnectedError, ClientConnectionError, ClientOSError
from asyncio import TimeoutError as AsyncTimeoutError
from circuitbreaker import circuit

from src.exceptions import ExternalServiceUnavailableException

logger = logging.getLogger(__name__)

CIRCUIT_BREAKER_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    AsyncTimeoutError,
    ClientConnectorError,
    ClientConnectionError,
    ServerDisconnectedError,
    ClientOSError,
    ExternalServiceUnavailableException,
)


circuit_breaker_standard = circuit(
    failure_threshold=3,
    recovery_timeout=30,
    expected_exception=CIRCUIT_BREAKER_EXCEPTIONS,
    name="external_service_standard"
)

circuit_breaker_strict = circuit(
    failure_threshold=2,
    recovery_timeout=60,
    expected_exception=CIRCUIT_BREAKER_EXCEPTIONS,
    name="external_service_strict"
)
