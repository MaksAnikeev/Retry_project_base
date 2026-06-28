import http

from .base import BaseDomainException

class ObjectNotFoundException(BaseDomainException):
    http_status_code = http.HTTPStatus.NOT_FOUND
    error_code = "OBJECT_NOT_FOUND"
    detail = "Object not found"

class UserNotFoundException(BaseDomainException):
    http_status_code = http.HTTPStatus.NOT_FOUND
    error_code = "USER_NOT_FOUND"
    detail = "User not found"

class TaskNotFoundException(BaseDomainException):
    http_status_code = http.HTTPStatus.NOT_FOUND
    error_code = "TASK_NOT_FOUND"
    detail = "Task not found"

class UserTaskNotFoundException(BaseDomainException):
    http_status_code = http.HTTPStatus.NOT_FOUND
    error_code = "USER_TASK_NOT_FOUND"
    detail = "Task not found for the specified user"