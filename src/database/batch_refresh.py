from collections import defaultdict
from typing import Any

from sqlalchemy import select, inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapper


async def batch_refresh(session: AsyncSession, *objects: Any) -> None:
    if not objects:
        return

    await session.flush()
    by_type: dict[type, list[Any]] = defaultdict(list)
    for obj in objects:
        by_type[type(obj)].append(obj)

    for model_cls, objs in by_type.items():
        mapper: Mapper = inspect(model_cls)
        pk_column = mapper.primary_key[0]
        ids = [getattr(obj, pk_column.name) for obj in objs]

        await session.execute(
            select(model_cls)
            .where(pk_column.in_(ids))
            .execution_options(populate_existing=True)
        )