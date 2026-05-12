from fastapi import FastAPI
from src.api.routers.user_routers import router as router_auth
from src.api.routers.task_routers import router as task_router


def init_routers(app_: FastAPI) -> None:
    app_.include_router(router_auth)
    app_.include_router(task_router)