import uuid
from datetime import datetime, UTC, timedelta

from sqlalchemy import or_, update, and_, select

from src.models import OutboxORM
from src.repositories.base import BaseRepository
from src.schemas.order_schemas import OrderGetSchema
from src.schemas.outbox_schemas import OutboxStatus


class OutboxRepository(BaseRepository[OutboxORM, OrderGetSchema]):
    model = OutboxORM

    async def claim_messages(
        self,
        limit: int,
        event_type: str,
        aggregate_type: str,
        lock_timeout_seconds: int = 300,
    ) -> list[OutboxORM]:
        now = datetime.now(UTC)
        claimed_at = now - timedelta(seconds=lock_timeout_seconds)

        ids_cte = (
            select(self.model.id)
            .where(
                or_(
                    and_(
                        self.model.status == OutboxStatus.PENDING,
                        or_(
                            self.model.next_attempt_at.is_(None),
                            self.model.next_attempt_at < now,
                        ),
                    ),
                    and_(
                        self.model.status == OutboxStatus.PROCESSING,
                        self.model.next_attempt_at < claimed_at,
                    ),
                ),
                self.model.event_type == event_type,
                self.model.aggregate_type == aggregate_type,
            )
            .order_by(self.model.created_at, self.model.id)
            .limit(limit)
            .cte("ids_to_claim")
        )

        stmt = (
            update(self.model)
            .where(self.model.id.in_(select(ids_cte)))
            .values(
                status=OutboxStatus.PROCESSING,
                next_attempt_at=now,
            )
            .returning(self.model)
        )

        result = await self.session.execute(stmt)
        claimed = list(result.scalars().all())
        return claimed