from datetime import datetime
from pydantic import BaseModel, Field


class PaginationParamsSchema(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    cursor: datetime | None = Field(
        default=None,
        description="Курсор — created_at последнего элемента с предыдущей страницы"
    )