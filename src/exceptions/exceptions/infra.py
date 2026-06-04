from .base import BaseDomainException

class ExternalServiceUnavailableException(BaseDomainException):
    http_status_code = 502
    error_code = "EXTERNAL_SERVICE_UNAVAILABLE"
    detail = "Task service is unavailable or returned an error"