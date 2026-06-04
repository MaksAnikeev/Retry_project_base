from fastapi import APIRouter, status
from starlette.responses import JSONResponse

from src.api.dependencies import ReportClientDep
from src.api.routers.health.utils import HealthDB
from src.utils.logging_decorator import log

router = APIRouter(tags=["Health"])


@router.get("/health", status_code=status.HTTP_200_OK)
@log("liveness_probe")
async def liveness_probe():
    return {"status": "ok", "service": "tasks-api"}


@router.get("/db_ready", status_code=status.HTTP_200_OK)
@log("db_readiness_probe")
async def db_readiness_probe():
    db_ok = await HealthDB.check_database()

    if not db_ok:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "checks": {
                    "database": "failed",
                }
            }
        )

    return {
        "status": "ok",
        "checks": {
            "database": "connected",
        }
    }


@router.get("/report_ready")
@log("report_readiness_probe")
async def report_readiness_probe(client: ReportClientDep):
    is_healthy = await client.check_health(timeout=3.0)

    if not is_healthy:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "check": "external_service_unreachable",
                "message": "Task service /health endpoint is not responding"
            }
        )

    return {"status": "ok", "checks": {"external_service": "healthy"}}