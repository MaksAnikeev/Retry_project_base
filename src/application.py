from fastapi.responses import UJSONResponse
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi import FastAPI
import sys
import logging
from pathlib import Path

from src.api import dependencies
from src.clients.report_http_client import ReportServiceClient
from src.config import settings
from src.api.routers.task_user_routers import router as task_user_router
from src.api.routers.health_routers import router as health_router
from src.exceptions import BaseDomainException
from src.exceptions.handlers import domain_exception_handler

sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)


def get_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        client = ReportServiceClient(
            base_url=settings.TASK_SERVICE_URL,
            timeout=30,
        )
        dependencies._report_client = client
        logging.info(f"Report client configured: {client.base_url}")

        try:
            yield
        finally:
            await client.close()
            dependencies._report_client = None
            logging.info("Application shutdown complete")


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

    app.include_router(task_user_router)
    app.include_router(health_router)

    app.add_exception_handler(BaseDomainException, domain_exception_handler)

    return app