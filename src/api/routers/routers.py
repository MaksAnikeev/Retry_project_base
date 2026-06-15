from fastapi import FastAPI

from src.api.routers.user_task_routers import router as user_task_router
from src.api.routers.health_routers import router as health_router


def register_routers(app: FastAPI) -> None:
    app.include_router(user_task_router)
    app.include_router(health_router)

