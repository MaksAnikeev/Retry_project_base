from src.exceptions.exceptions.base import BaseDomainException
from src.exceptions.exceptions.not_found import ObjectNotFoundException, UserNotFoundException, TaskNotFoundException, UserTaskNotFoundException
from src.exceptions.exceptions.conflict import AlreadyExistsException, TaskAlreadyExistsException, UserAlreadyExistsException
from src.exceptions.exceptions.validation import (
    MissingRequiredFieldsException, NotAllowedFieldException, EmptyPasswordException,
    AtLeastOneFieldRequiredException, EmptyRequestBodyException
)
from src.exceptions.exceptions.infra import ExternalServiceUnavailableException

__all__ = [
    "BaseDomainException",
    "ObjectNotFoundException", "UserNotFoundException", "TaskNotFoundException", "UserTaskNotFoundException",
    "AlreadyExistsException", "TaskAlreadyExistsException", "UserAlreadyExistsException",
    "MissingRequiredFieldsException", "NotAllowedFieldException", "EmptyPasswordException",
    "AtLeastOneFieldRequiredException", "EmptyRequestBodyException",
    "ExternalServiceUnavailableException",
]
