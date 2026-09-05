from typing import Annotated

from fastapi import Depends

from src.database.db import SessionDep
from src.database.unit_of_work import UnitOfWork


def get_uow(session: SessionDep) -> UnitOfWork:
    return UnitOfWork(session=session)

UowDep = Annotated[UnitOfWork, Depends(get_uow)]
