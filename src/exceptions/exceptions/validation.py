from .base import BaseDomainException

class MissingRequiredFieldsException(BaseDomainException):
    http_status_code = 422
    error_code = "MISSING_REQUIRED_FIELDS"
    detail = "Missing required parameters"

class NotAllowedFieldException(BaseDomainException):
    http_status_code = 422
    error_code = "NOT_ALLOWED_FIELD"
    detail = "Invalid or not allowed parameters for update"

class EmptyPasswordException(BaseDomainException):
    http_status_code = 400
    error_code = "EMPTY_PASSWORD"
    detail = "Password cannot be empty"

class AtLeastOneFieldRequiredException(BaseDomainException):
    http_status_code = 400
    error_code = "AT_LEAST_ONE_FIELD_REQUIRED"
    detail = "At least one field must be provided"

class EmptyRequestBodyException(BaseDomainException):
    http_status_code = 400
    error_code = "EMPTY_REQUEST_BODY"
    detail = "Request body cannot be empty"