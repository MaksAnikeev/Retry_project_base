from src.exceptions.base import BaseDomainException
from src.exceptions.db_integrity import UniqueConstraintViolationException
from src.exceptions.external_service import ExternalServiceUnavailableException, ExternalServiceClientException
from src.exceptions.kafka_exception import KafkaProducerNotStartedError
from src.exceptions.kafka_exception import KafkaException

from src.exceptions.not_found import ObjectNotFoundException
from src.exceptions.already_exists import AlreadyExistsException
from src.exceptions.validation import (
    MissingRequiredFieldsException, NotAllowedFieldException,
    AtLeastOneFieldRequiredException, EmptyRequestBodyException, EmptyFiledException
)

__all__ = [
    "BaseDomainException",
    "ObjectNotFoundException",
    "AlreadyExistsException",
    "UniqueConstraintViolationException",
    "MissingRequiredFieldsException", "NotAllowedFieldException", "EmptyFiledException",
    "AtLeastOneFieldRequiredException", "EmptyRequestBodyException",
    "ExternalServiceUnavailableException", "ExternalServiceClientException"
    "KafkaProducerNotStartedError",
    "KafkaException"
]
