from fastapi import HTTPException

class CustomException(Exception):
    detail: str = "Неожиданная ошибка"

    def __init__(self, *args, **kwargs):
        super().__init__(self.detail, *args, **kwargs)


class ObjectNotFoundException(CustomException):
    detail = "Объект с такими параметрами не найден"


class AlreadyExistedException(CustomException):
    detail = "Объект с такими параметрами уже существует"


class NotAllNecessaryParamsException(CustomException):
    detail = "Переданы не все необходимые параметры"


class NotAllowedParameterException(CustomException):
    detail = "Указаны неверные параметры для изменения"


class EmptyAttributesException(CustomException):
    detail = (
        "Переданный атрибут не может быть пустым или все переданный атрибуты пустые"
    )


class CustomHTTPException(HTTPException):
    status_code = 500
    detail: str | None = None

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)

class ObjectNotFoundHTTPException(CustomHTTPException):
    status_code = 404
    detail = "Объект не найден"

class UserNotFoundHTTPException(CustomHTTPException):
    status_code = 404
    detail = "Пользователь с таким id не найден"

class UserTaskNotFoundHTTPException(CustomHTTPException):
    status_code = 404
    detail = "У пользователя не найдена задача с таким ид"

class TaskNotFoundHTTPException(CustomHTTPException):
    status_code = 404
    detail = "Задача с таким id не найдена"


class TaskAlreadyExistedHTTPException(CustomHTTPException):
    status_code = 409
    detail = "Задача с таким названием уже существует"


class UserAlreadyExistedHTTPException(CustomHTTPException):
    status_code = 409
    detail = "Пользователь с таким email уже существует"


class UserNotExistedHTTPException(CustomHTTPException):
    status_code = 401
    detail = "Пользователь с таким email не найден. Необходима регистрация."


class NotAllowedParameterHTTPException(CustomHTTPException):
    status_code = 422
    detail = (
        "У данного объекта нет параметров/атрибутов, которые вы хотите изменить."
        " Уточните название изменяемых атрибутов"
    )


class EmptyPasswordHTTPException(CustomHTTPException):
    status_code = 400
    detail = "Пароль не может быть пустым"


class NotAnyAttributeHTTPException(CustomHTTPException):
    status_code = 400
    detail = "Хотя бы одно поле должно быть непустым"


class EmptyRequestBodyHTTPException(CustomHTTPException):
    status_code = 400
    detail = "Не передано ни одного параметра"


class TaskServiceErrorHTTPException(CustomHTTPException):
    status_code = 502
    detail = "Сервис задач недоступен или вернул ошибку"


class CircuitBreakerError(Exception):
    """Исключение, когда цепь разомкнута"""
    pass