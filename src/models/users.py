import typing

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base

if typing.TYPE_CHECKING:
    from src.models import TasksORM


class UsersORM(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(), nullable=True)
    email: Mapped[str] = mapped_column(
        String(200), nullable=False, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean)
    hashed_password: Mapped[str] = mapped_column(String(200), nullable=False)

    tasks: Mapped[list["TasksORM"]] = relationship(
        back_populates="user",
    )
