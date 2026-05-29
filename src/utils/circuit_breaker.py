import logging
import asyncio
from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Awaitable, Any
from aiohttp import ClientConnectorError, ServerDisconnectedError, ClientConnectionError, ClientOSError
from asyncio import TimeoutError as AsyncTimeoutError

from src.exceptions.exceptions import CircuitBreakerError

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Состояния Circuit Breaker"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        name: str = "default",
        expected_exceptions: tuple = (
                ConnectionError,
                TimeoutError,
                ClientConnectorError,
                ClientConnectionError,
                ServerDisconnectedError,
                AsyncTimeoutError,
                ClientOSError,
        )
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name
        self.expected_exceptions = expected_exceptions

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: datetime | None = None
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        return self._state

    async def call(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """
        Выполняет функцию с защитой circuit breaker.
        """
        async with self._lock:
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._state = CircuitState.HALF_OPEN
                    logger.warning(f"🔓 [{self.name}] Circuit breaker: HALF-OPEN (тестовый запрос)")
                else:
                    logger.error(f"🔴 [{self.name}] Circuit breaker: OPEN — запрос отклонён")
                    raise CircuitBreakerError(f"Circuit breaker '{self.name}' is OPEN")

        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result

        except self.expected_exceptions as e:
            await self._on_failure()
            raise
        except Exception as e:
            logger.warning(f"⚠️ [{self.name}] Неожиданная ошибка (не считается для CB): {type(e).__name__}")
            raise

    async def _on_success(self):
        async with self._lock:
            self._failure_count = 0
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.CLOSED
                logger.info(f"✅ [{self.name}] Circuit breaker: CLOSED (восстановлен)")

    async def _on_failure(self):
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.now()

            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.error(
                    f"🔴 [{self.name}] Circuit breaker: OPEN "
                    f"({self._failure_count} ошибок, порог={self.failure_threshold})"
                )

    def _should_attempt_reset(self) -> bool:
        if not self._last_failure_time:
            return True
        return datetime.now() - self._last_failure_time >= timedelta(seconds=self.recovery_timeout)

    def get_stats(self) -> dict:
        """Статистика для мониторинга"""
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "threshold": self.failure_threshold,
            "last_failure": self._last_failure_time.isoformat() if self._last_failure_time else None,
        }