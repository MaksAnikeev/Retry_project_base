import uuid
from datetime import datetime, timezone

from sqlalchemy import select, or_

from src.models import OutboxORM
from src.repositories.base import BaseRepository
from src.schemas.order_schemas import OrderGetSchema
from src.schemas.outbox_schemas import OutboxStatus


class OutboxRepository(BaseRepository[OutboxORM, OrderGetSchema]):
    model = OutboxORM

    async def get_pending_order_messages(
        self,
        event_type: str,
        aggregate_type: str,
        limit: int = 50,
        cursor_id: uuid.UUID | None = None,
    ) -> list[OutboxORM]:
        now = datetime.now(timezone.utc)
        stmt = (
            select(self.model)
            .where(
                self.model.status == OutboxStatus.PENDING.value,
                self.model.event_type == event_type,
                self.model.aggregate_type == aggregate_type,
                or_(
                    self.model.next_attempt_at.is_(None),
                    self.model.next_attempt_at < now,
                ),
            )
            .order_by(self.model.id)
            .with_for_update(skip_locked=True)
            .limit(limit)
        )
        if cursor_id is not None:
            stmt = stmt.where(self.model.id > cursor_id)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())
