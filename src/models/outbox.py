import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    Index,
    Integer,
    String,
    Uuid,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.models import Base


class OutboxORM(Base):
    __tablename__ = "outbox_messages"

    topic: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    aggregate_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    aggregate_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        nullable=True,
        index=True,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        server_default="pending",
        nullable=False,
        comment="Статус сообщения: pending, completed, failed",
    )
    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    next_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Когда сообщение было успешно отправлено в Kafka",
    )
    last_error: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
        comment="Последняя ошибка при отправке",
    )

    __table_args__ = (
        Index(
            "ix_outbox_status_created_at_id",
            "status",
            "created_at",
            "id",
        ),
    )
