import json
from typing import Callable

from pydantic import BaseModel, Field, ConfigDict


class KafkaProducerConfig(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    key_serializer: Callable = Field(
        default=lambda k: k.encode("utf-8") if k else None,
    )
    acks: int = -1
    enable_idempotence: bool = True
    compression_type: str = "gzip"

    def to_producer(self) -> dict:
        return self.model_dump(mode="python", exclude_none=True)

kafka_producer_config = KafkaProducerConfig()