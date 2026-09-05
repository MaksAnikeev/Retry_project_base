from datetime import date, timedelta

from src.models import TaskORM, UserORM


async def get_users_with_tasks_data() -> list[UserORM]:
    today = date.today()
    user1 = UserORM(
        username="user_one",
        email="user1@test.com",
        hashed_password="hashed_password_1",
        is_active=True,
        tasks=[
            TaskORM(
                title="Задача пользователя 1",
                description="Единственная задача первого юзера",
                finish_date=today + timedelta(days=7),
                done=False,
                complexity="easy",
                estimated_hours=2.0,
                priority="medium",
                report_status="completed",
                attempts=1,
            ),
        ],
    )

    user2 = UserORM(
        username="user_two",
        email="user2@test.com",
        hashed_password="hashed_password_2",
        is_active=True,
        tasks=[
            TaskORM(
                title="Первая задача юзера 2",
                description="Описание первой",
                finish_date=today + timedelta(days=3),
                done=False,
                complexity="hard",
                estimated_hours=8.0,
                priority="high",
                report_status="completed",
                attempts=2,
            ),
            TaskORM(
                title="Вторая задача юзера 2",
                description="Описание второй",
                finish_date=today + timedelta(days=10),
                done=True,
                complexity="medium",
                estimated_hours=4.0,
                priority="medium",
                report_status="completed",
                attempts=1,
            ),
            TaskORM(
                title="Третья задача юзера 2",
                description="Описание третьей",
                finish_date=today + timedelta(days=14),
                done=False,
                complexity="easy",
                estimated_hours=1.5,
                priority="low",
                report_status="pending",
                attempts=0,
            ),
        ],
    )
    return [user1, user2]
