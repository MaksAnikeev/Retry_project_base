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
        except asyncio.TimeoutError:
            logging.error(f"Health check: Database connection TIMEOUT after {HealthDB.HEALTH_CHECK_TIMEOUT}s")
            return False
        except Exception as e:
            logging.error(f"Health check: Database connection failed - {type(e).__name__}: {e}")
            return False
