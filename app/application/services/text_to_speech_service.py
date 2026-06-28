import os
import uuid
import asyncio
import logging
from openai import AsyncOpenAI
from app.config import settings
from app.application.services.temp_file_manager import TempFileManager

logger = logging.getLogger(__name__)

from app.infrastructure.repositories.system_settings_repository import SystemSettingsRepository

class TextToSpeechService:
    """Async text-to-speech wrapper natively utilizing OpenAI TTS bounds."""

    def __init__(self, system_settings_repository: SystemSettingsRepository = None):
        self.system_settings_repository = system_settings_repository
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.current_api_key = settings.OPENAI_API_KEY
        self.model = settings.TTS_MODEL
        self.voice = settings.TTS_VOICE

    async def _ensure_client(self):
        if self.system_settings_repository:
            sys_settings = await self.system_settings_repository.get_settings()
            db_key = sys_settings.openai_api_key
            if db_key and db_key != self.current_api_key:
                self.current_api_key = db_key
                self.client = AsyncOpenAI(api_key=self.current_api_key)

    async def synthesize_speech(self, text: str) -> str:
        """
        Convert logical output text to speech asynchronously natively.
        Saves output as .ogg (opus) so WhatsApp renders it as an inline voice note.
        """
        if not text or len(text.strip()) == 0:
            raise ValueError("TTS Text buffer cannot be inherently empty.")

        logger.info(f"Synthesizing logical speech: {len(text)} chars utilizing {self.voice}")
        await self._ensure_client()

        try:
            response = await self.client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=text,
                response_format="opus"
            )

            # Store the resulting output audio down memory
            output_dir = settings.AUDIO_TEMP_DIR
            
            def _ensure_dir_and_write(response_obj, file_path, d_dir):
                os.makedirs(d_dir, exist_ok=True)
                with open(file_path, 'wb') as f:
                    for chunk in response_obj.iter_bytes():
                        f.write(chunk)
            
            filename = f"tts_out_{uuid.uuid4()}.ogg"
            output_path = os.path.join(output_dir, filename)

            # Write audio bytes to disk in thread to prevent blocking loop
            await asyncio.to_thread(_ensure_dir_and_write, response, output_path, output_dir)

            logger.info(f"Speech synthesized to physical payload memory: {output_path}")
            
            return output_path

        except Exception as e:
            logger.error(f"TTS failed completely: {e}", exc_info=True)
            raise ValueError(f"Text-to-speech engine failed dynamically: {str(e)}")
