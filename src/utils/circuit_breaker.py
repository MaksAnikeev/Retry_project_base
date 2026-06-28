import logging
from circuitbreaker import circuit

from src.exceptions import ExternalServiceUnavailableException

logger = logging.getLogger(__name__)

CIRCUIT_BREAKER_EXCEPTIONS = (
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
