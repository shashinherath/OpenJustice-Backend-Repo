from abc import ABC, abstractmethod
import uuid
from typing import Optional

class IAuditLogRepository(ABC):
    """Interface for logging security and audit trails."""

    @abstractmethod
    async def log_action(
        self,
        user_id: uuid.UUID | None,
        action: str,
        entity: str | None = None,
        entity_id: int | None = None,
        metadata: dict | None = None
    ) -> None:
        """Logs an action performed by a user."""
        pass

    @abstractmethod
    async def get_recent_activities(self, limit: int = 5) -> list:
        """Fetch the most recent audit logs."""
        pass
