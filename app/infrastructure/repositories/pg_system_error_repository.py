import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.domain.interfaces.system_error_repository import ISystemErrorRepository
from app.infrastructure.models.system_error import SystemError

class PgSystemErrorRepository(ISystemErrorRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_error(
        self,
        error_type: str,
        message: str,
        details: str
    ) -> uuid.UUID:
        error_record = SystemError(
            error_type=error_type,
            message=message,
            details=details
        )
        self.session.add(error_record)
        await self.session.commit()
        await self.session.refresh(error_record)
        return error_record.id

    async def get_errors(self, skip: int = 0, limit: int = 100) -> tuple[int, list[SystemError]]:
        # Count total
        count_query = select(func.count(SystemError.id))
        total = await self.session.scalar(count_query) or 0

        # Fetch paginated logs
        query = (
            select(SystemError)
            .order_by(desc(SystemError.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        errors = list(result.scalars().all())
        
        return total, errors

    async def get_stats(self) -> dict:
        query = select(SystemError.error_type, func.count(SystemError.id)).group_by(SystemError.error_type)
        result = await self.session.execute(query)
        
        stats = {
            "total": 0,
            "llm": 0,
            "db": 0,
            "api": 0,
            "auth": 0,
            "system": 0
        }
        
        for error_type, count in result:
            stats["total"] += count
            et = error_type.lower()
            if et in stats:
                stats[et] += count
            else:
                stats[et] = count
                
        return stats
