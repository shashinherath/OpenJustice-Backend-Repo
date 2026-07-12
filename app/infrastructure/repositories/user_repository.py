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

    async def get_by_verification_token(self, token: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email_verification_token == token))
        return result.scalars().first()

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_total_count(self) -> int:
        from sqlalchemy import func
        result = await self.db.execute(select(func.count(User.id)))
        return result.scalar_one_or_none() or 0

    async def list_users(self, skip: int = 0, limit: int = 100, search_query: Optional[str] = None, role: Optional[str] = None, status: Optional[str] = None) -> list[User]:
        from sqlalchemy import or_
        
        stmt = select(User)
        
        if search_query:
            term = f"%{search_query}%"
            stmt = stmt.where(
                or_(
                    User.first_name.ilike(term),
                    User.last_name.ilike(term),
                    User.email.ilike(term),
                    User.phone_number.ilike(term)
                )
            )
            
        if role and role.lower() != "all":
            stmt = stmt.where(User.role == role.lower())
            
        if status and status.lower() != "all":
            is_active = status.lower() == "active"
            stmt = stmt.where(User.is_active == is_active)
            
        stmt = stmt.order_by(User.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_status(self, user_id: UUID, is_active: bool) -> Optional[User]:
        user = await self.get_by_uuid(user_id)
        if user:
            user.is_active = is_active
            await self.db.commit()
            await self.db.refresh(user)
        return user

    async def update_profile(
        self,
        user_id: UUID,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        preferred_language: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> Optional[User]:
        """Update user profile fields."""
        user = await self.get_by_uuid(user_id)
        if not user:
            return None

        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if email is not None:
            user.email = email
        if preferred_language is not None:
            user.preferred_language = preferred_language
        if avatar_url is not None:
            user.avatar_url = avatar_url

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def set_password(self, user_id: UUID, hashed_password: str) -> Optional[User]:
        """Update user password."""
        user = await self.get_by_uuid(user_id)
        if not user:
            return None

        user.hashed_password = hashed_password
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_active_sessions_count(self) -> int:
        from sqlalchemy import func
        from app.infrastructure.models.user_session import UserSession
        result = await self.db.execute(
            select(func.count(UserSession.id)).where(UserSession.expires_at > func.now())
        )
        return result.scalar_one_or_none() or 0
