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
