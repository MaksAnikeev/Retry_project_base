import typing
import uuid
from datetime import date

from sqlalchemy import String, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if typing.TYPE_CHECKING:
    from src.models import UserORM


class TaskORM(Base):
    __tablename__ = "tasks"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None]
    done: Mapped[bool]
    finish_date: Mapped[date] = mapped_column(Date(), nullable=False)
    complexity: Mapped[str] = mapped_column(String(50))
    estimated_hours: Mapped[float]
    priority: Mapped[str] = mapped_column(String(50))

    user: Mapped["UserORM"] = relationship("UserORM", back_populates="tasks")

    model_config = {"from_attributes": True}
