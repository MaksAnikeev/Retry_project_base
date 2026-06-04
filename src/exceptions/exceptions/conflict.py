from .base import BaseDomainException

class AlreadyExistsException(BaseDomainException):
    http_status_code = 409
    error_code = "ALREADY_EXISTS"
    detail = "Object already exists"

class TaskAlreadyExistsException(BaseDomainException):
    http_status_code = 409
    error_code = "TASK_ALREADY_EXISTS"
    detail = "Task with this title already exists"

class UserAlreadyExistsException(BaseDomainException):
    http_status_code = 409
    error_code = "USER_ALREADY_EXISTS"
    detail = "User with this email already exists"