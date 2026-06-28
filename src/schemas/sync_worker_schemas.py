from pydantic import BaseModel, Field


class SyncStatsSchema(BaseModel):
    processed: int = Field(default=0, description="Количество обработанных задач")
    updated: int = Field(default=0, description="Количество успешно обновлённых задач")
