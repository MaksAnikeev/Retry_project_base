import uuid
from datetime import datetime, UTC, timedelta

from sqlalchemy import or_, update, and_, select

from src.models import OutboxORM
from src.repositories.base import BaseRepository
from src.schemas.outbox_schemas import OutboxStatus


class OutboxRepository(BaseRepository[OutboxORM]):
    model = OutboxORM

    async def claim_messages(
        self,
        limit: int,
        event_type: str,
        aggregate_type: str,
        lock_timeout_seconds: int = 300,
    ) -> tuple[list[OutboxORM], uuid.UUID]:
        now = datetime.now(UTC)
        stale_lock_threshold = now - timedelta(seconds=lock_timeout_seconds)
        batch_attempt_id = uuid.uuid4()

        stmt = (
            select(self.model)
            .where(
                or_(
                    and_(
                        self.model.status == OutboxStatus.PENDING,
                        or_(
                            self.model.next_attempt_at.is_(None),
                            self.model.next_attempt_at <= now,
                        ),
                    ),
                    and_(
                        self.model.status == OutboxStatus.PROCESSING,
                        self.model.processing_started_at < stale_lock_threshold,
                    ),
                ),
                self.model.event_type == event_type,
                self.model.aggregate_type == aggregate_type,
            )
            .order_by(self.model.created_at, self.model.id)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self.session.execute(stmt)
        claimed = list(result.scalars().all())

        if not claimed:
            return [], batch_attempt_id

        claimed_ids = [m.id for m in claimed]
        await self.session.execute(
            update(self.model)
            .where(self.model.id.in_(claimed_ids))
            .values(
                status=OutboxStatus.PROCESSING,
                processing_started_at=now,
                attempt_id=batch_attempt_id,
            )
        )
        return claimed, batch_attempt_id

    async def mark_completed(
        self,
        message_ids: list[uuid.UUID],
        expected_attempt_id: uuid.UUID,
    ) -> int:
        now = datetime.now(UTC)
        stmt = (
            update(self.model)
            .where(
                self.model.id.in_(message_ids),
                self.model.attempt_id == expected_attempt_id,
                self.model.status == OutboxStatus.PROCESSING,
            )
            .values(
                status=OutboxStatus.COMPLETED,
                sent_at=now,
                last_error=None,
                processing_started_at=None
            )
        )
        result = await self.session.execute(stmt)
        return result.rowcount

    async def mark_failed_with_retry(
        self,
        message_id: uuid.UUID,
        error_message: str,
        expected_attempt_id: uuid.UUID,
        max_attempts: int,
        backoff_base_seconds: int,
    ) -> bool:
        now = datetime.now(UTC)
        stmt = (
                select(self.model.attempts)
                .where(
                    self.model.id == message_id,
                    self.model.attempt_id == expected_attempt_id,
                    self.model.status == OutboxStatus.PROCESSING,
            )
        )
        current = await self.session.execute(stmt)
        attempts_row = current.scalar_one_or_none()

        if attempts_row is None:
            return False

        new_attempts = attempts_row + 1
        if new_attempts >= max_attempts:
            new_status = OutboxStatus.FAILED
            new_next_attempt = None
        else:
            new_status = OutboxStatus.PENDING
            delay = backoff_base_seconds * (2 ** (new_attempts - 1))
            new_next_attempt = now + timedelta(seconds=delay)
        result = await self.session.execute(
            update(self.model)
            .where(
                self.model.id == message_id,
                self.model.attempt_id == expected_attempt_id,
                self.model.attempts == attempts_row,
            )
            .values(
                status=new_status,
                attempts=new_attempts,
                next_attempt_at=new_next_attempt,
                last_error=error_message[:2000],
                attempt_id=None,
                processing_started_at=None
            )
        )
        return result.rowcount > 0