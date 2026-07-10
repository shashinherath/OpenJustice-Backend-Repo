import uuid
from typing import Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.interfaces.user_session_repository import IUserSessionRepository
from app.infrastructure.models.user_session import UserSession

class PgUserSessionRepository(IUserSessionRepository):
    """PostgreSQL implementation of UserSession tracking."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(
        self,
        user_id: uuid.UUID,
        session_token: uuid.UUID,
        channel: str,
        ip_address: str | None,
        user_agent: str | None
    ) -> uuid.UUID:
        expires = datetime.now(timezone.utc) + timedelta(days=7) # 7 day session
        session_record = UserSession(
            user_id=user_id,
            session_token=session_token,
            channel=channel,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.now(timezone.utc),
            expires_at=expires
        )
        self.session.add(session_record)
        await self.session.flush()
        return session_record.id

    async def invalidate_session(self, session_token: uuid.UUID) -> None:
        from sqlalchemy import delete
        await self.session.execute(
            delete(UserSession).where(UserSession.session_token == session_token)
        )
        await self.session.commit()
