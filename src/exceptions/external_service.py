import http

from .base import BaseDomainException


class ExternalServiceUnavailableException(BaseDomainException):
    http_status_code = http.HTTPStatus.SERVICE_UNAVAILABLE
    error_code = "EXTERNAL_SERVICE_UNAVAILABLE"
    detail = "External service is temporarily unavailable, retry later"


class ExternalServiceClientException(BaseDomainException):
    http_status_code = http.HTTPStatus.BAD_REQUEST  # 400
    error_code = "EXTERNAL_SERVICE_CLIENT_ERROR"
    detail = "External service rejected the request due to invalid data"