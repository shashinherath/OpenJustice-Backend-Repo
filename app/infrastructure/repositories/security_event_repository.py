"""SecurityEvent repository implementation."""
from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.security_event import SecurityEvent


class SecurityEventRepository:
    """Data access layer for security events."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_recent_events(self, limit: int = 5) -> List[SecurityEvent]:
        """Fetch the most recent security events."""
        result = await self.db.execute(
            select(SecurityEvent).order_by(SecurityEvent.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def get_priority_alerts(self, limit: int = 3) -> List[SecurityEvent]:
        """Fetch priority alerts."""
        result = await self.db.execute(
            select(SecurityEvent)
            .where(
                or_(
                    SecurityEvent.is_priority == True,
                    SecurityEvent.severity.in_(["Critical", "High"])
                )
            )
            .order_by(SecurityEvent.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_count_by_area(self, area: str, hours: int = 24) -> int:
        """Count events in a specific area within the last N hours."""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        result = await self.db.execute(
            select(func.count(SecurityEvent.id))
            .where(
                SecurityEvent.area == area,
                SecurityEvent.created_at >= since
            )
        )
        return result.scalar_one_or_none() or 0

    async def get_count_by_condition(self, condition, hours: int = 24) -> int:
        """Count events using a custom condition within the last N hours."""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        result = await self.db.execute(
            select(func.count(SecurityEvent.id))
            .where(
                condition,
                SecurityEvent.created_at >= since
            )
        )
        return result.scalar_one_or_none() or 0

    async def create(self, event: SecurityEvent) -> SecurityEvent:
        self.db.add(event)
        await self.db.flush()
        await self.db.refresh(event)
        return event

    async def get_total_count(self) -> int:
        result = await self.db.execute(select(func.count(SecurityEvent.id)))
        return result.scalar_one_or_none() or 0
