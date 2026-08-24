from httpx import AsyncClient
from sqlalchemy import select

from src.models import OrderORM, OutboxORM


async def test_add_orders(
    setup_db,
    async_session_factory_null_pull,
    ac: AsyncClient,
):
    payload = [
        {
                "user_id": "de662447-4321-4922-9f88-16150f295c99",
                "product_name": "Удочка",
                "price": 1500000,
                "quantity": 2
        },
    ]
    response = await ac.post("/orders", json=payload)
    assert response.status_code == 200
    if response.status_code == 200:
        orders = response.json()
        order = orders[0]
        assert order["product_name"] == "Удочка"

        async with async_session_factory_null_pull() as session:
            stmt = select(OrderORM)
            result = await session.execute(stmt)
            orders = result.scalars().all()
            assert len(orders) == 3

            stmt = select(OutboxORM).where(
                OutboxORM.aggregate_id == order["id"]
            )
            result = await session.execute(stmt)
            outbox_entries = result.scalars().all()
            assert len(outbox_entries) == 1
            outbox = outbox_entries[0]
            assert outbox.event_type == "OrderCreated"
            assert outbox.payload is not None
            assert outbox.status == "pending"
