import logging
from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._is_active = False

    @property
    def is_active(self) -> bool:
        return self._is_active

    async def __aenter__(self) -> Self:
        self._is_active = True
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:

        if exc_type is not None:
            await self.rollback()
            logger.warning(
                "Transaction rolled back",
                extra={"error": str(exc_val), "error_type": exc_type.__name__},
            )
        else:
            await self.commit()

    async def commit(self) -> None:
        if self._is_active:
            await self.session.commit()
            self._is_active = False

    async def rollback(self) -> None:
        if self._is_active:
            await self.session.rollback()
            self._is_active = False
