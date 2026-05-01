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
