import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from aiokafka import AIOKafkaProducer

from src.exceptions.kafka_exception import KafkaProducerNotStartedError


class KafkaProducerClient:

    def __init__(self, bootstrap_servers: str | None = None) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.logger = logging.getLogger(self.__class__.__name__)
        self._producer: AIOKafkaProducer | None = None

    def _get_producer(self) -> AIOKafkaProducer:
        if self._producer is None:
            raise KafkaProducerNotStartedError(
                detail=f"Kafka producer for {self.bootstrap_servers} is not started"
            )
        return self._producer

    async def start(self) -> None:
        if self._producer is not None:
            self.logger.warning("Kafka producer is already started")
            return

        self._producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            acks=-1,
            enable_idempotence=True,
            compression_type="gzip",
        )
        await self._producer.start()
        self.logger.info(
            "Kafka producer started",
            extra={"bootstrap_servers": self.bootstrap_servers},
        )

    async def stop(self) -> None:
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None
            self.logger.info("Kafka producer stopped")

    async def send_message(
        self,
        topic: str,
        value: dict[str, Any],
        key: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        _producer = self._get_producer()

        kafka_headers = None
        if headers:
            kafka_headers = [(k, v.encode("utf-8")) for k, v in headers.items()]

        await self._producer.send_and_wait(
            topic=topic,
            value=value,
            key=key,
            headers=kafka_headers,
        )

    @asynccontextmanager
    async def lifespan(self) -> AsyncIterator["KafkaProducerClient"]:
        await self.start()
        try:
            yield self
        finally:
            await self.stop()
