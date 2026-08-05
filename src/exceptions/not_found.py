import http

from .base import BaseDomainException

class ObjectNotFoundException(BaseDomainException):
    http_status_code = http.HTTPStatus.NOT_FOUND
    error_code = "OBJECT_NOT_FOUND"
    detail = "Object not found"
