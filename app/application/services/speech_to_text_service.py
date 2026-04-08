import logging
import asyncio
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

class SpeechToTextService:
    """Async speech-to-text wrapper utilizing OpenAI Whisper API."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.WHISPER_MODEL

    async def transcribe_audio(self, audio_file_path: str) -> str:
        """
        Transcribe audio file to text asynchronously natively via the Whisper API.
        Automatically detects language natively within Whisper.
        """
        logger.info(f"Transcribing audio sequence: {audio_file_path}")

        try:
            # Whisper handles MP3, MP4, MPEG, MPGA, M4A, WAV, and WEBM
            with open(audio_file_path, 'rb') as audio_file:
                response = await self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    response_format="text"
                )

            logger.info("WhatsApp transcription successful.")
            return str(response).strip()

        except Exception as e:
            logger.error(f"Transcription failed entirely: {e}", exc_info=True)
            raise ValueError(f"OpenAI Whisper crashed trying to convert audio: {str(e)}")
