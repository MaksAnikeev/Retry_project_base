from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi import FastAPI
import sys
import logging
from pathlib import Path
from src.api.routers.user_task_routers import router as user_task_router
from src.api.routers.health_routers import router as health_router
from src.clients.report_http_client import create_report_client
from src.config import get_settings
from src.exceptions import BaseDomainException
from src.exceptions.handlers.handlers import domain_exception_handler
from src.utils.logging_config import setup_logging

sys.path.append(str(Path(__file__).parent.parent))

settings = get_settings()

logger = logging.getLogger(__name__)
setup_logging(level=settings.LOG_LEVEL)


def _register_routers(app: FastAPI) -> None:
    app.include_router(user_task_router)
    app.include_router(health_router)


def _register_middlewares(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=False,
        allow_methods=['*'],
        allow_headers=['*'],
    )

def _register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(BaseDomainException, domain_exception_handler)


def get_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.report_client = create_report_client()
        logger.info(
            "Report client initialized",
            extra={"base_url": app.state.report_client.base_url},
        )
        logger.info("Application started")

        try:
            yield
        finally:
            await app.state.report_client.close()
            app.state.report_client = None
            logger.info("Application shutdown complete")


    app = FastAPI(
        docs_url='/docs',
        openapi_url='/openapi.json',
        lifespan=lifespan
    )

    _register_routers(app)
    _register_middlewares(app)
    _register_exception_handlers(app)

    return app