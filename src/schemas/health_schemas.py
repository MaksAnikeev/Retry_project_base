from enum import StrEnum
from pydantic import BaseModel, Field

class HealthStatus(StrEnum):
    OK = "ok"
    ERROR = "error"

class HealthResponse(BaseModel):
    status: HealthStatus = Field(description="Общий статус системы")
    checks: dict[str, str] = Field(description="Статус отдельных компонентов (например, {'database': 'connected'})")
    message: str | None = Field(default=None, description="Дополнительное сообщение об ошибке, если статус ERROR")

class LivenessResponse(BaseModel):
    status: HealthStatus = Field(default=HealthStatus.OK, description="Статус сервиса")
    service: str = Field(description="Название микросервиса")