from typing import Annotated

from fastapi import Depends
from starlette.requests import Request

from src.db import async_session_factory
from src.exceptions import (
    NotAccessTokenHTTPException,
    WrongAccessTokenHTTPException,
    WrongAccessToken,
    TimeoutAccessToken,
    TimeoutAccessTokenHTTPException,
)
from src.services.auth import AuthService
from src.utils.db_manager import DBManager


def get_token(request: Request) -> str:
    access_token = request.cookies.get("access_token", None)
    if not access_token:
        raise NotAccessTokenHTTPException
    return access_token


def get_current_user_id(token: str = Depends(get_token)) -> int:
    try:
        data = AuthService().get_data_from_hash(token)
    except TimeoutAccessToken:
        raise TimeoutAccessTokenHTTPException
    except WrongAccessToken:
        raise WrongAccessTokenHTTPException

    return data["user_id"]


UserIDDep = Annotated[int, Depends(get_current_user_id)]


async def get_db():
    async with DBManager(session_factory=async_session_factory) as db:
        yield db


DBDep = Annotated[DBManager, Depends(get_db)]
