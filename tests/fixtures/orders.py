
from src.models import OrderORM


async def get_orders_data() -> list[OrderORM]:
    order1 = OrderORM(
            user_id="c54e6396-d7d2-4d53-bece-51c91990fa5b",
            product_name="Велосипед",
            description="Крутой горный велик",
            price=6500000,
            quantity=1
    )

    order2 = OrderORM(
            user_id="c54e6396-d7d2-4d53-bece-51c91990fa5b",
            product_name="Колесо для велосипеда",
            price=500000,
            quantity=3
    )
    return [order1, order2]
