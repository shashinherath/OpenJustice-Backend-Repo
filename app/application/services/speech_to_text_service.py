import logging
import asyncio
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

from app.infrastructure.repositories.system_settings_repository import SystemSettingsRepository

class SpeechToTextService:
    """Async speech-to-text wrapper utilizing OpenAI Whisper API."""

    def __init__(self, system_settings_repository: SystemSettingsRepository = None):
        self.system_settings_repository = system_settings_repository
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.current_api_key = settings.OPENAI_API_KEY
        self.model = settings.WHISPER_MODEL

    async def _ensure_client(self):
        if self.system_settings_repository:
            sys_settings = await self.system_settings_repository.get_settings()
            db_key = sys_settings.openai_api_key
            if db_key and db_key != self.current_api_key:
                self.current_api_key = db_key
                self.client = AsyncOpenAI(api_key=self.current_api_key)

    async def transcribe_audio(self, audio_file_path: str) -> str:
        """
        Transcribe audio file to text asynchronously natively via the Whisper API.
        Automatically detects language natively within Whisper.
        """
        logger.info(f"Transcribing audio sequence: {audio_file_path}")
        await self._ensure_client()

        try:
            # Whisper handles MP3, MP4, MPEG, MPGA, M4A, WAV, and WEBM
            def _read_audio():
                with open(audio_file_path, 'rb') as f:
                    return f.read()

            audio_bytes = await asyncio.to_thread(_read_audio)
            import os
            filename = os.path.basename(audio_file_path)
            
            # Send to Whisper
            response = await self.client.audio.transcriptions.create(
                model=self.model,
                file=(filename, audio_bytes),
                response_format="text"
            )

            logger.info("WhatsApp transcription successful.")
            return str(response).strip()

        except Exception as e:
            logger.error(f"Transcription failed entirely: {e}", exc_info=True)
            raise ValueError(f"OpenAI Whisper crashed trying to convert audio: {str(e)}")
