import functools
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError


def log(
    operation_name: str,
) -> Callable:

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        logger = logging.getLogger(func.__module__)

        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()

            logger.info(f"{operation_name} started | arguments: {_safe_repr(kwargs)}")

            try:
                result = await func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                logger.debug(
                    f"{operation_name} completed | duration: "
                    + f" {duration:.2f}ms | arguments: {_safe_repr(kwargs)}",
                )
                return result

            except HTTPException as e:
                logger.warning(
                    f"{operation_name} failed | status: {e.status_code} | detail: {e.detail}"
                )
                raise
            except IntegrityError as e:
                logger.warning(
                    f"{operation_name} integrity error | constraint: {getattr(e.orig, 'constraint_name', 'unknown')}"
                )
                raise
            except Exception as e:
                logger.error(
                    f"{operation_name} error | type: {type(e).__name__} | message: {str(e)}",
                    exc_info=True,
                )
                raise
        return wrapper
    return decorator


def _safe_repr(obj: Any, max_len: int = 500) -> str:
    SECRET_KEYS = {"password", "token", "secret", "hashed_password", "api_key", "authorization"}

    def process(item: Any) -> Any:
        if isinstance(item, BaseModel):
            return process(item.model_dump())
        elif isinstance(item, dict):
            return {
                k: "***" if k.lower() in SECRET_KEYS else process(v)
                for k, v in item.items()
            }
        elif isinstance(item, (list, tuple)):
            return [process(i) for i in item]
        else:
            return item
    safe_obj = process(obj)
    repr_str = repr(safe_obj)
    return repr_str[:max_len] + "..." if len(repr_str) > max_len else repr_str