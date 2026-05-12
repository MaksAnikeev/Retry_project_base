from fastapi import HTTPException

class CustomException(Exception):
    detail: str = "Неожиданная ошибка"

    def __init__(self, *args, **kwargs):
        super().__init__(self.detail, *args, **kwargs)


class ObjectNotFoundException(CustomException):
    detail = "Объект с такими параметрами не найден"


class UserNotFoundException(CustomException):
    detail = "Пользователь с таким ид не найден"


class TaskNotFoundException(CustomException):
    detail = "Задача с таким ид не найден"


class AlreadyExistedException(CustomException):
    detail = "Объект с такими параметрами уже существует"


class TooLongParameterException(CustomException):
    detail = "Вводимый параметр недопустимо длинный"


class TooManyObjectsException(CustomException):
    detail = (
        "По данным параметрам найдено несколько объектов, уточните параметры поиска"
    )


class NotAllNecessaryParamsException(CustomException):
    detail = "Переданы не все необходимые параметры"


class NotAllowedParameterException(CustomException):
    detail = "Указаны неверные параметры для изменения"


class IncorrectPasswordException(CustomException):
    detail = "Введен некорректный пароль"


class WrongAccessToken(CustomException):
    detail = "Некорректный токен."


class TimeoutAccessToken(CustomException):
    detail = "Время действия токена истекло."


class EmptyAttributesException(CustomException):
    detail = (
        "Переданный атрибут не может быть пустым или все переданный атрибуты пустые"
    )


class CustomHTTPException(HTTPException):
    status_code = 500
    detail: str | None = None

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)


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


class IncorrectPasswordHTTPException(CustomHTTPException):
    status_code = 401
    detail = "Неверно указан логин или пароль"


class NotAccessTokenHTTPException(CustomHTTPException):
    status_code = 401
    detail = "Необходимо залогиниться"


class WrongAccessTokenHTTPException(CustomHTTPException):
    status_code = 401
    detail = "Необходимо залогиниться"


class TimeoutAccessTokenHTTPException(CustomHTTPException):
    status_code = 401
    detail = "Время действия токена истекло. Необходимо залогиниться"


class TooLongParameterHTTPException(CustomHTTPException):
    status_code = 400
    detail = "Вводимый параметр недопустимо длинный, проверьте правильность ввода всех параметров ИД"


class TooManyObjectsHTTPException(CustomHTTPException):
    status_code = 422
    detail = (
        "Поиск осуществляется не по уникальным параметрам,"
        " в результате по данным параметрам найдено несколько объектов, уточните параметры поиска"
    )


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
