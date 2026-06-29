import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.interfaces.audit_log_repository import IAuditLogRepository
from app.infrastructure.models.audit_log import AuditLog

class PgAuditLogRepository(IAuditLogRepository):
    """PostgreSQL implementation of Audit Logging."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_action(
        self,
        user_id: uuid.UUID | None,
        action: str,
        entity: str | None = None,
        entity_id: int | None = None,
        metadata: dict | None = None
    ) -> None:
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            metadata_=metadata
        )
        self.session.add(audit_entry)
        await self.session.commit()

    async def get_recent_activities(self, limit: int = 5) -> list:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        result = await self.session.execute(
            select(AuditLog).options(selectinload(AuditLog.user)).order_by(AuditLog.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
