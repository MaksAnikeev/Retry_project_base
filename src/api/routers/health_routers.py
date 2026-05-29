from fastapi import APIRouter, status

from src.services.health_service import HealthService

router = APIRouter(tags=["Health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def liveness_probe():
    """
    Liveness Probe
    """
    return {"status": "ok", "service": "tasks-api"}


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_probe():
    """
    Readiness Probe
    """
    db_ok = await HealthService.check_database()

    if not db_ok:
        return {
            "status": "error",
            "checks": {
                "database": "failed",
            }
        }, status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ok",
        "checks": {
            "database": "connected",
        }
    }