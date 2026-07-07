import typing
import uuid
from datetime import date

from sqlalchemy import String, ForeignKey, Date, UniqueConstraint, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if typing.TYPE_CHECKING:
    from src.models import UserORM


class TaskORM(Base):
    __tablename__ = "tasks"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None]
    finish_date: Mapped[date] = mapped_column(Date(), nullable=False)
    done: Mapped[bool]
    complexity: Mapped[str | None] = mapped_column(String(50))
    estimated_hours: Mapped[float | None] = mapped_column(Float)
    priority: Mapped[str | None] = mapped_column(String(20))
    report_status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        server_default="pending",
        nullable=False,
        comment="Статус отчёта: pending, completed, failed",
    )

    user: Mapped["UserORM"] = relationship("UserORM", back_populates="tasks")

    __table_args__ = (
        UniqueConstraint("user_id", "title", name="uq_tasks_user_title"),
    )
