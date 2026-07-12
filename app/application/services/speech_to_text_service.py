import logging
import asyncio
import traceback
from openai import AsyncOpenAI

from app.config import settings
from app.application.services.system_error_logger import log_system_error
from app.infrastructure.repositories.system_settings_repository import SystemSettingsRepository

logger = logging.getLogger(__name__)

class SpeechToTextService:
    """Async speech-to-text wrapper utilizing OpenAI Whisper API."""

    def __init__(self, system_settings_repository: SystemSettingsRepository | None = None, storage_handler=None):
        self.system_settings_repository = system_settings_repository
        self.storage_handler = storage_handler
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
            import tempfile
            import os
            
            local_file_path = audio_file_path
            temp_file = None
            
            if self.storage_handler and audio_file_path.startswith("http"):
                ext = audio_file_path.split('.')[-1].lower()
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
                local_file_path = temp_file.name
                temp_file.close()
                download_success = await self.storage_handler.download_file(audio_file_path, local_file_path)
                if not download_success:
                    raise ValueError("Failed to download audio file from storage.")

            # Whisper handles MP3, MP4, MPEG, MPGA, M4A, WAV, and WEBM
            def _read_audio():
                with open(local_file_path, 'rb') as f:
                    return f.read()

            audio_bytes = await asyncio.to_thread(_read_audio)
            filename = os.path.basename(local_file_path)
            
            # Send to Whisper
            response = await self.client.audio.transcriptions.create(
                model=self.model,
                file=(filename, audio_bytes),
                response_format="text"
            )

            logger.info("WhatsApp transcription successful.")
            return str(response).strip()

        except Exception as e:
            await log_system_error(
                error_type="API",
                message="Speech-to-Text transcription provider failed.",
                details=f"Model: {self.model}\n{traceback.format_exc()}"
            )
            logger.error(f"Transcription failed entirely: {e}", exc_info=True)
            raise ValueError(f"OpenAI Whisper crashed trying to convert audio: {str(e)}")
        finally:
            if 'temp_file' in locals() and temp_file and 'os' in locals() and os.path.exists(local_file_path):
                try:
                    os.unlink(local_file_path)
                except Exception as cleanup_err:
                    logger.error(f"Failed to clean up temp audio file {local_file_path}: {cleanup_err}")
