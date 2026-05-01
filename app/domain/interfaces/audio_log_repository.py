from abc import ABC, abstractmethod
import uuid
from typing import Optional

class IAudioLogRepository(ABC):
    """Interface for tracking voice AI telemetry."""

    @abstractmethod
    async def log_audio_request(
        self,
        user_id: uuid.UUID,
        audio_type: str,
        language: Optional[str],
        duration_seconds: float,
        provider: str
    ) -> uuid.UUID:
        """Logs STT or TTS processing details."""
        pass
