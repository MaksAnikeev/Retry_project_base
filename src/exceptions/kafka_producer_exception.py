from src.exceptions.base_kafka_exception import BaseKafkaException


class KafkaProducerNotStartedError(BaseKafkaException):
    error_code = "KAFKA_PRODUCER_NOT_STARTED"
    detail = "Kafka producer is not started. Call start() or use lifespan context manager."