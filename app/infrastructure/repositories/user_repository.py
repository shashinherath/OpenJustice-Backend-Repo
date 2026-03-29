"""User repository implementation."""
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.user_repository import IUserRepository
from app.infrastructure.models.user import User


class UserRepository(IUserRepository):
    """Data access layer for users."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def get_by_phone(self, phone_number: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.phone_number == phone_number)
        )
        return result.scalars().first()

    async def get_by_uuid(self, user_uuid: UUID) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.uuid == user_uuid))
        return result.scalars().first()

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user
