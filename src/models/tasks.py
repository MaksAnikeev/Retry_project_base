import typing
from datetime import date

from sqlalchemy import String, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base

if typing.TYPE_CHECKING:
    from src.models import UsersORM


class TasksORM(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None]
    done: Mapped[bool]
    finish_date: Mapped[date] = mapped_column(Date(), nullable=False)

    user: Mapped["UsersORM"] = relationship(back_populates="tasks")
