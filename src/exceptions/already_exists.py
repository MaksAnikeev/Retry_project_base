import http

from .base import BaseDomainException

class AlreadyExistsException(BaseDomainException):
    http_status_code = http.HTTPStatus.CONFLICT
    error_code = "ALREADY_EXISTS"
    detail = "Object already exists"
