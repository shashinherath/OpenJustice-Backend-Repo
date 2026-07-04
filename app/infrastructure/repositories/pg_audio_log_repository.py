import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.interfaces.audio_log_repository import IAudioLogRepository
from app.infrastructure.models.audio_request import AudioRequest

class PgAudioLogRepository(IAudioLogRepository):
    """PostgreSQL implementation of Audio Log Repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_audio_request(
        self,
        user_id: uuid.UUID,
        audio_type: str,
        language: Optional[str],
        duration_seconds: float,
        provider: str
    ) -> uuid.UUID:
        audio_log = AudioRequest(
            user_id=user_id,
            audio_type=audio_type,
            language=language,
            duration_seconds=duration_seconds,
            provider=provider
        )
        self.session.add(audio_log)
        await self.session.flush() # flush to get the ID
        return audio_log.id

    async def get_logs(self, skip: int = 0, limit: int = 100) -> tuple[int, list]:
        from sqlalchemy import select, func
        total_result = await self.session.execute(select(func.count(AudioRequest.id)))
        total = total_result.scalar_one_or_none() or 0
        
        result = await self.session.execute(
            select(AudioRequest).order_by(AudioRequest.created_at.desc()).offset(skip).limit(limit)
        )
        logs = list(result.scalars().all())
        return total, logs

    async def get_stats(self) -> dict:
        from sqlalchemy import select, func
        
        result = await self.session.execute(
            select(
                func.count(AudioRequest.id),
                func.avg(AudioRequest.duration_seconds)
            )
        )
        
        count, avg_duration = result.first() or (0, 0)
        return {
            "completed": int(count or 0),
            "avg_latency": float(avg_duration or 0) * 1000.0,
            "total_latency": float(avg_duration or 0) * 1000.0 * int(count or 0),
            "latency_count": int(count or 0)
        }
