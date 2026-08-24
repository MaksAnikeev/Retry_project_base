from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.application import get_app
from src.config import settings
from src.database.db import get_session
from src.dependencies.dependencies_tasks import get_report_client
from src.models import *  # noqa
from src.repositories.order_rep import OrderRepository
from src.repositories.user_rep import UsersRepository
from tests.data_to_tests.orders import get_orders_data
from tests.data_to_tests.users_tasks import get_users_with_tasks_data

app = get_app()

@pytest.fixture(scope="session")
async def async_engine_null_pull():
    engine = create_async_engine(
        url=settings.DATABASE_URL_asyncpg,
        echo=False,
        poolclass=NullPool,
    )
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
def async_session_factory_null_pull(async_engine_null_pull) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=async_engine_null_pull,
        class_=AsyncSession,
        expire_on_commit=False,
    )

@pytest.fixture(scope="session", autouse=True)
async def check_test():
    assert settings.MODE == "TEST", f"Опасность! MODE={settings.MODE}, а должен быть TEST"


@pytest.fixture(autouse=True)
def override_app_dependencies(async_session_factory_null_pull) -> AsyncGenerator[None, None]:
    async def _test_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_factory_null_pull() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    app.dependency_overrides[get_session] = _test_get_session
    # возвращает этот ответ на любой запрос к внешнему сервису отчетов
    # async def post_reports_batch_side_effect(requests):
    #     reports = []
    #     for req in requests:
    #         reports.append(TaskAPIResponseSchema(
    #             task_id=req.task_id,
    #             complexity="hard",
    #             estimated_hours=8.5,
    #             priority="high",
    #         ))
    #     return reports
    #
    # mock.post_reports_batch.side_effect = post_reports_batch_side_effect

    app.dependency_overrides[get_report_client] = lambda: AsyncMock()
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="session", autouse=True)
async def setup_db(check_test, async_engine_null_pull, async_session_factory_null_pull):
    async with async_engine_null_pull.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with async_session_factory_null_pull() as session:
        user_rep = UsersRepository(session=session)
        users_data = await get_users_with_tasks_data()
        await user_rep.add_many(users_data)
        await session.commit()
        order_rep = OrderRepository(session=session)
        orders_data = await get_orders_data()
        await order_rep.add_many(orders_data)
        await session.commit()
    yield


@pytest.fixture(scope="session")
async def ac() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

