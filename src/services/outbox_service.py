import logging

from src.models import OutboxORM
from src.repositories.outbox_rep import OutboxRepository


class OutboxService:

    def __init__(
        self,
        outbox_repo: OutboxRepository,
    ) -> None:
        self.outbox_repo = outbox_repo

        self.logger = logging.getLogger(self.__class__.__name__)

    async def publish_events(self, outboxes_orm: list[OutboxORM]) -> None:
        await self.outbox_repo.add_many(outboxes_orm)