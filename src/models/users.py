import typing

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if typing.TYPE_CHECKING:
    from src.models import TaskORM


class UserORM(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(), nullable=True)
    email: Mapped[str] = mapped_column(
        String(200), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean)
    is_deleted: Mapped[bool] = mapped_column(Boolean)
    hashed_password: Mapped[str] = mapped_column(String(200), nullable=False)

    tasks: Mapped[list["TaskORM"]] = relationship(
        "TaskORM",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    model_config = {"from_attributes": True}
