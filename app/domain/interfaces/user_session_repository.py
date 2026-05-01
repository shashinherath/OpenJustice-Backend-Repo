from abc import ABC, abstractmethod
import uuid
from typing import Optional

class IUserSessionRepository(ABC):
    """Interface for managing user sessions."""

    @abstractmethod
    async def create_session(
        self,
        user_id: uuid.UUID,
        session_token: uuid.UUID,
        channel: str,
        ip_address: str | None,
        user_agent: str | None
    ) -> uuid.UUID:
        """Stores a new session token and returns the session record ID."""
        pass

    @abstractmethod
    async def invalidate_session(self, session_token: uuid.UUID) -> None:
        """Invalidates a session token."""
        pass
