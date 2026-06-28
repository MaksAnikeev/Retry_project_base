from enum import StrEnum
from pydantic import BaseModel, Field


class HealthStatus(StrEnum):
    OK = "ok"
    ERROR = "error"


class LivenessResponse(BaseModel):
    status: HealthStatus = Field(default=HealthStatus.OK, description="Статус сервиса")
    service: str = Field(description="Название микросервиса")


class ComponentStatus(BaseModel):
    name: str = Field(description="Название компонента")
    status: HealthStatus = Field(description="Статус компонента")
    message: str | None = Field(default=None, description="Сообщение об ошибке")


class ReadinessResponse(BaseModel):
    status: HealthStatus = Field(description="Общий статус готовности")
    service: str = Field(description="Название микросервиса")
    components: list[ComponentStatus] = Field(description="Информация по компонентам")
