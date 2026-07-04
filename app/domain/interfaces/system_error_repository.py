from abc import ABC, abstractmethod
import uuid
from typing import Optional
from app.infrastructure.models.system_error import SystemError

class ISystemErrorRepository(ABC):
    """Interface for system error logging and retrieval."""

    @abstractmethod
    async def log_error(
        self,
        error_type: str,
        message: str,
        details: str
    ) -> uuid.UUID:
        """Logs a new system error and returns its ID."""
        pass

    @abstractmethod
    async def get_errors(self, skip: int = 0, limit: int = 100) -> tuple[int, list[SystemError]]:
        """Gets a paginated list of system errors, returning total count and list of errors."""
        pass

    @abstractmethod
    async def get_stats(self) -> dict:
        """
        Retrieves global statistics for system errors.
        Returns a dictionary like:
        {
            "total": int,
            "llm": int,
            "db": int,
            "api": int,
            "auth": int,
            "system": int
        }
        """
        pass
