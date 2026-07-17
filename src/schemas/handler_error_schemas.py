from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error_code: str = Field(description="Уникальный код ошибки")
    message: str = Field(description="Сообщение об ошибке")
    path: str = Field(description="URL-путь, на котором произошла ошибка")
