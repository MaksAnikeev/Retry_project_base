import logging

from tenacity import retry, stop_after_attempt, retry_if_exception_type, wait_exponential_jitter

from src.config import settings
from src.exceptions import ExternalServiceUnavailableException

logger = logging.getLogger(__name__)


NETWORK_EXCEPTIONS = (
    ExternalServiceUnavailableException,
)

def get_retry(
    quantity_attempts: int = settings.STOP_RETRY_AFTER_ATTEMPT_BASE,
    wait_interval: int = settings.EXPONENTIAL_JITTER_INTERVAL_BASE,
    max_wait: int = settings.EXPONENTIAL_JITTER_MAX_BASE,
):
    return retry(
        stop=stop_after_attempt(quantity_attempts),
        wait=wait_exponential_jitter(
            initial=wait_interval,
            max=max_wait,
            exp_base=settings.EXPONENTIAL_JITTER_EXP_BASE,
            jitter=settings.EXPONENTIAL_JITTER_BASE),
        retry=retry_if_exception_type(NETWORK_EXCEPTIONS),
        reraise=True,
        before_sleep=lambda rs: logger.warning(
            f"🔁 RETRY {rs.attempt_number}/{quantity_attempts} | "
            f"wait={rs.idle_for:.1f}s | "
            f"error={type(rs.outcome.exception()).__name__}"
        ),
    )

retry_standard = get_retry()
retry_fast = get_retry(quantity_attempts=2, wait_interval=1, max_wait=20)