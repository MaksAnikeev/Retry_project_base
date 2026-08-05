import http

from src.exceptions import BaseDomainException


class UniqueConstraintViolationException(BaseDomainException):
    http_status_code = http.HTTPStatus.CONFLICT
    error_code = "UNIQUE_CONSTRAINT_VIOLATION"
    detail = "Entity with this value already exists"