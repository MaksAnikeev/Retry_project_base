from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class OutboxStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class OutboxClaimedSchema(BaseModel):
    id: UUID
    topic: str
    event_type: str
    aggregate_type: str
    aggregate_id: UUID
    payload: dict[str, Any]
    attempt_id: UUID
    attempts: int
    created_at: datetime
    processing_started_at: datetime | None = None