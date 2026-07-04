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

    @abstractmethod
    async def get_logs(self, skip: int = 0, limit: int = 100) -> tuple[int, list]:
        """Returns total count and list of AudioRequest objects for traceability."""
        pass

    @abstractmethod
    async def get_stats(self) -> dict:
        """Returns total count and avg latency for audio logs."""
        pass
