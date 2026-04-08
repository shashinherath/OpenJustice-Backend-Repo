import os
import uuid
import asyncio
import logging
from openai import AsyncOpenAI
from app.config import settings
from app.application.services.temp_file_manager import TempFileManager

logger = logging.getLogger(__name__)

class TextToSpeechService:
    """Async text-to-speech wrapper natively utilizing OpenAI TTS bounds."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.TTS_MODEL
        self.voice = settings.TTS_VOICE

    async def synthesize_speech(self, text: str) -> str:
        """
        Convert logical output text to speech asynchronously natively.
        Saves output as .ogg (opus) so WhatsApp renders it as an inline voice note.
        """
        if not text or len(text.strip()) == 0:
            raise ValueError("TTS Text buffer cannot be inherently empty.")

        logger.info(f"Synthesizing logical speech: {len(text)} chars utilizing {self.voice}")

        try:
            response = await self.client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=text,
                response_format="opus"
            )

            # Store the resulting output audio down memory
            output_dir = settings.AUDIO_TEMP_DIR
            os.makedirs(output_dir, exist_ok=True)
            
            filename = f"tts_out_{uuid.uuid4()}.ogg"
            output_path = os.path.join(output_dir, filename)

            # Write audio bytes to disk — iter_bytes() is a sync generator in openai SDK
            with open(output_path, 'wb') as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)

            logger.info(f"Speech synthesized to physical payload memory: {output_path}")
            
            # Autocleanup policy appended to output as well, deleting it after Twilio hits it
            TempFileManager.schedule_deletion(output_path)
            
            return output_path

        except Exception as e:
            logger.error(f"TTS failed completely: {e}", exc_info=True)
            raise ValueError(f"Text-to-speech engine failed dynamically: {str(e)}")
