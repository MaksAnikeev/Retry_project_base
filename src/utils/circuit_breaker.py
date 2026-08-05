import logging
from circuitbreaker import circuit

from src.config import settings
from src.exceptions import ExternalServiceUnavailableException

logger = logging.getLogger(__name__)

CIRCUIT_BREAKER_EXCEPTIONS = (
    ExternalServiceUnavailableException,
)


circuit_breaker_standard = circuit(
    failure_threshold=settings.CB_FAILURE_THRESHOLD_STANDARD,
    recovery_timeout=settings.CB_RECOVERY_TIMEOUT_STANDARD,
    expected_exception=CIRCUIT_BREAKER_EXCEPTIONS,
    name="external_service_standard"
)