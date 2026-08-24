import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from aiokafka import AIOKafkaProducer

from src.exceptions import KafkaProducerNotStartedError
from src.kafka.config import KafkaProducerConfig


class KafkaProducerClient:

    def __init__(
        self,
        bootstrap_servers: str,
        config: KafkaProducerConfig,
    ) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self._producer: AIOKafkaProducer | None = None
        self._lock = asyncio.Lock()

    def _get_producer(self) -> AIOKafkaProducer:
        if self._producer is None:
            raise KafkaProducerNotStartedError(
                detail=f"Kafka producer for {self.bootstrap_servers} is not started"
            )
        return self._producer

    async def start(self) -> None:
        if self._producer is not None:
            return

        async with self._lock:
            if self._producer is not None:
                return

            producer_config = self.config.to_producer()

            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                **producer_config
            )
            try:
                await self._producer.start()
            except Exception:
                self._producer = None
                raise

            self.logger.info(
                "Kafka producer started",
                extra={"bootstrap_servers": self.bootstrap_servers},
            )

    async def stop(self) -> None:
        async with self._lock:
            if self._producer is None:
                return
            producer = self._producer
            self._producer = None

            try:
                await producer.stop()
                self.logger.info("Kafka producer stopped")
            except Exception as e:
                self.logger.warning(
                    "Error while stopping Kafka producer",
                    extra={"error": str(e)},
                )

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
