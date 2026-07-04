import logging
import traceback
from app.infrastructure.db.base import async_session_maker
from app.infrastructure.repositories.pg_system_error_repository import PgSystemErrorRepository

logger = logging.getLogger(__name__)

async def log_system_error(error_type: str, message: str, details: str = None) -> None:
    """
    Safely logs a system error to the database using an isolated session.
    This ensures that errors are captured even if the surrounding request
    transaction rolls back due to the same exception.
    """
    try:
        async with async_session_maker() as session:
            repo = PgSystemErrorRepository(session)
            await repo.log_error(
                error_type=error_type,
                message=message,
                details=details or ""
            )
    except Exception as e:
        logger.error(f"Failed to log system error to database: {e}\n{traceback.format_exc()}")
