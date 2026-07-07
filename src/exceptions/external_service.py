import http

from .base import BaseDomainException

class ExternalServiceUnavailableException(BaseDomainException):
    http_status_code = http.HTTPStatus.BAD_GATEWAY
    error_code = "EXTERNAL_SERVICE_UNAVAILABLE"
    detail = "Report service is unavailable or returned an error"


class ExternalServiceClientException(BaseDomainException):
    http_status_code = http.HTTPStatus.BAD_GATEWAY
    error_code = "EXTERNAL_SERVICE_CLIENT_ERROR"
    detail = "External service rejected the request"