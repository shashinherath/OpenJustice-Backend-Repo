"""Repository interface for user persistence."""
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.infrastructure.models.user import User


class IUserRepository(ABC):
    """Contract for user repositories."""

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_phone(self, phone_number: str) -> Optional[User]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_uuid(self, user_uuid: UUID) -> Optional[User]:
        raise NotImplementedError
