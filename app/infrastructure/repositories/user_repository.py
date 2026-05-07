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
        result = await self.db.execute(select(User).where(User.id == user_uuid))
        return result.scalars().first()

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_total_count(self) -> int:
        from sqlalchemy import func
        result = await self.db.execute(select(func.count(User.id)))
        return result.scalar_one_or_none() or 0

    async def list_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        result = await self.db.execute(
            select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def update_status(self, user_id: UUID, is_active: bool) -> Optional[User]:
        user = await self.get_by_uuid(user_id)
        if user:
            user.is_active = is_active
            await self.db.commit()
            await self.db.refresh(user)
        return user
