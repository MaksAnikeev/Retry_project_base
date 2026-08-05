import logging
from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def __aenter__(self) -> Self:
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
                "Transaction rolled back due to exception",
                extra={"error": str(exc_val), "error_type": exc_type.__name__},
            )
        else:
            await self.commit()

    async def commit(self) -> None:
        if self.session.in_transaction():
            await self.session.commit()

    async def rollback(self) -> None:
        if self.session.in_transaction():
            await self.session.rollback()
