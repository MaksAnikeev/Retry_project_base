import http

from src.exceptions import BaseDomainException


class DatabaseConstraintException(BaseDomainException):
    http_status_code = http.HTTPStatus.CONFLICT
    error_code = "DATABASE_CONSTRAINT"
    detail = "Database constraint violation"