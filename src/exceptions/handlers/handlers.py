from fastapi import Request
from fastapi.responses import JSONResponse

from src.exceptions.base import BaseDomainException
from src.schemas.handler_error_schemas import ErrorResponse


async def domain_exception_handler(request: Request, exc: BaseDomainException):
    error_response = ErrorResponse(
        error_code=exc.error_code,
        message=exc.detail,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=exc.http_status_code,
        content=error_response.model_dump(),
    )
