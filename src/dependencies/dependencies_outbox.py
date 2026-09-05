from typing import Annotated

from fastapi import Depends

from src.repositories.outbox_rep import OutboxRepository
from src.services.outbox_service import OutboxService

from src.database.db import SessionDep


def get_outbox_rep(session: SessionDep) -> OutboxRepository:
    return OutboxRepository(session=session)

OutboxRepDep = Annotated[OutboxRepository, Depends(get_outbox_rep)]

def get_outbox_service(
    outbox_repo: OutboxRepDep,
) -> OutboxService:
    return OutboxService(
        outbox_repo=outbox_repo,
    )

OutboxServiceDep = Annotated[OutboxService, Depends(get_outbox_service)]
