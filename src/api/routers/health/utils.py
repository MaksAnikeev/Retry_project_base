import asyncio
import logging

from sqlalchemy import text

from src.db import async_session_factory


class HealthDB:
    HEALTH_CHECK_TIMEOUT = 5.0

    @staticmethod
    async def check_database() -> bool:
        try:
            async with async_session_factory() as session:
                await asyncio.wait_for(
                    session.execute(text("SELECT 1")),
                    timeout=HealthDB.HEALTH_CHECK_TIMEOUT
                )
                return True
        except Exception:
            logging.warning("Health check: Database connection failed")
            return False
