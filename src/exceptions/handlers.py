from fastapi import Request
from fastapi.responses import JSONResponse
from src.exceptions.exceptions.base import BaseDomainException

async def domain_exception_handler(request: Request, exc: BaseDomainException):
    return JSONResponse(
        status_code=exc.http_status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.detail,
            "path": request.url.path
        }
    )