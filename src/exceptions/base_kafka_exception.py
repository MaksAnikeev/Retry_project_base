import http

from src.exceptions.base import BaseDomainException


class BaseKafkaException(BaseDomainException):
    http_status_code = http.HTTPStatus.SERVICE_UNAVAILABLE
    error_code = "KAFKA_ERROR"
    detail = "Kafka service error"
