from fastapi.responses import UJSONResponse
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi import FastAPI
import sys
import logging
from pathlib import Path

from src.api import dependencies
from src.clients.http_client import TaskServiceClient
from src.config import settings
from src.api.routers.user_routers import router as user_router
from src.api.routers.task_routers import router as task_router
from src.api.routers.health_routers import router as health_router
from src.utils.circuit_breaker import CircuitBreaker

sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)


def get_app() -> FastAPI:
    """
    Get FastAPI application.
    This is the main constructor of an application.
    :return: application.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        async with TaskServiceClient(
            base_url=settings.TASK_SERVICE_URL,
            timeout=30,
        ) as client:
            dependencies._task_client = client
            logging.info(f"✅ HTTP Client ready: {client.base_url}")

            dependencies._task_service_cb = CircuitBreaker(
                name="task_service",
                failure_threshold=3,
                recovery_timeout=30,
            )
            logging.info("✅ CircuitBreaker ready: task_service")

            yield
            dependencies._task_client = None
            dependencies._task_service_cb = None


    app = FastAPI(
        docs_url='/docs',
        openapi_url='/openapi.json',
        default_response_class=UJSONResponse,
        lifespan=lifespan
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=False,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    app.include_router(user_router)
    app.include_router(task_router)
    app.include_router(health_router)

    return app