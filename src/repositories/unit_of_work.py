import logging
from collections import defaultdict
from types import TracebackType
from typing import Self, Any

from sqlalchemy import select
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

    async def flush_and_refresh(self, *objects: Any) -> None:
        if not objects:
            return
        await self.session.flush()
        by_type: dict[type, list[Any]] = defaultdict(list)
        for obj in objects:
            by_type[type(obj)].append(obj)
        for model_cls, objs in by_type.items():
            pk_column = model_cls.__mapper__.primary_key[0]
            ids = [getattr(obj, pk_column.name) for obj in objs]
            await self.session.execute(
                select(model_cls)
                .where(pk_column.in_(ids))
                .execution_options(populate_existing=True)
            )