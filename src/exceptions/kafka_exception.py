import http

from src.exceptions.base import BaseDomainException


class KafkaException(BaseDomainException):
    http_status_code = http.HTTPStatus.SERVICE_UNAVAILABLE
    error_code = "KAFKA_ERROR"
    detail = "Kafka service error"


class KafkaProducerNotStartedError(KafkaException):
    error_code = "KAFKA_PRODUCER_NOT_STARTED"
    detail = "Kafka producer is not started. Call start() or use lifespan context manager."
