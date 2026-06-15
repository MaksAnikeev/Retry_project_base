from fastapi import APIRouter, status
from starlette.responses import JSONResponse

from src.api.dependencies import ReportClientDep
from src.api.routers.health.utils import HealthDB
from src.schemas.health_schemas import HealthResponse, HealthStatus, LivenessResponse
from src.utils.logging_decorator import log

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    response_model=LivenessResponse,
    summary="Liveness probe: проверка, что процесс приложения запущен"
)
async def liveness_probe():
    return LivenessResponse(
        status=HealthStatus.OK,
        service="tasks-api",
    )


@router.get(
    "/db_ready",
    status_code=status.HTTP_200_OK,
    response_model=HealthResponse,
    summary="Проверка готовности базы данных"
)
@log("db_readiness_probe")
async def db_readiness_probe():
    db_ok = await HealthDB.check_database()
    response = HealthResponse(
        status=HealthStatus.OK if db_ok else HealthStatus.ERROR,
        checks={"database": "connected" if db_ok else "failed"}
    )
    if not db_ok:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response.model_dump())
    return response


@router.get(
    "/report_ready",
    status_code=status.HTTP_200_OK,
    response_model=HealthResponse,
    summary="Проверка готовности внешнего сервиса отчетов"
)
@log("report_readiness_probe")
async def report_readiness_probe(client: ReportClientDep):
    is_healthy = await client.check_health(timeout=3.0)

    if not is_healthy:
        response = HealthResponse(
            status=HealthStatus.ERROR,
            checks={"external_service": "unreachable"},
            message="Task service /health endpoint is not responding"
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response.model_dump()
        )
    return HealthResponse(
        status=HealthStatus.OK,
        checks={"external_service": "healthy"}
    )