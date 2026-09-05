import asyncio
import logging

from aiokafka import AIOKafkaProducer

from src.exceptions import KafkaProducerNotStartedError
from src.kafka.config import KafkaProducerConfig
from src.mappers.kafka_mapper import headers_to_kafka_format, payload_to_bytes
from src.schemas.kafka_schemas import BaseKafkaMessageSchema


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
        self._started = False

    async def start(self) -> None:
        if self._started:
            return

        async with self._lock:
            if self._started:
                return

            producer_config = self.config.to_producer()
            producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                **producer_config
            )
            try:
                await producer.start()
            except Exception:
                raise

            self._producer = producer
            self._started = True

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
            self._started = False
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
        message: BaseKafkaMessageSchema
    ) -> None:
        async with self._lock:
            if not self._started or self._producer is None:
                raise KafkaProducerNotStartedError(
                    "Kafka producer is not started. Call start() first."
                )
            producer = self._producer
        kafka_value = payload_to_bytes(message.payload)
        kafka_headers = headers_to_kafka_format(message.headers)

        await producer.send_and_wait(
            topic=message.topic,
            value=kafka_value,
            key=message.key,
            headers=kafka_headers,
        )
