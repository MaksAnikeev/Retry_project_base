from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from sqlalchemy import NullPool, func, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.config import settings

async_engine: AsyncEngine = create_async_engine(url=settings.DATABASE_URL_asyncpg, echo=False, pool_pre_ping=True)
async_engine_null_pull = create_async_engine(
    url=settings.DATABASE_URL_asyncpg,
    echo=False,
    poolclass=NullPool,
)

async_session_factory = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)
async_session_factory_null_pull = async_sessionmaker(
    bind=async_engine_null_pull, expire_on_commit=False
)

class Base(DeclarativeBase):
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )