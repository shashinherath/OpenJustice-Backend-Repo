import os
import uuid
import asyncio
from datetime import datetime
import logging
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

class TempFileManager:
    """Manages raw Audio binary memory and Twilio downloads."""

    @staticmethod
    async def download_twilio_audio(media_url: str) -> str:
        """Download remote Twilio mobile audio block internally for local Whisper consumption."""
        os.makedirs(settings.AUDIO_TEMP_DIR, exist_ok=True)
        
        # Twilio whatsapp audio usually comes back as OGG files by default.
        filename = f"twilio_in_{uuid.uuid4()}.ogg"
        file_path = os.path.join(settings.AUDIO_TEMP_DIR, filename)

        try:
            # Twilio media usually requires HTTP Basic Auth with Account SID and Auth Token 
            # if "Secure Media" is explicitly enabled, otherwise it serves publicly on hard unguessable URLs.
            auth = None
            if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
                auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(media_url, auth=auth)
                response.raise_for_status()

                with open(file_path, 'wb') as f:
                    f.write(response.content)

                logger.info(f"Successfully downloaded secure media from WhatsApp to {file_path}")
                
                # Cleanup memory
                TempFileManager.schedule_deletion(file_path)
                return file_path
                
        except Exception as e:
            logger.error(f"Failed to fetch secure media audio from Twilio {media_url}: {e}", exc_info=True)
            raise ValueError(f"Error proxing incoming WhatsApp voicenote: {e}")

    @staticmethod
    def schedule_deletion(file_path: str):
        """Creates a background thread natively to scrub physical server payload after configuration timeouts."""
        asyncio.create_task(TempFileManager._delete_after_delay(file_path, settings.AUDIO_RETENTION_MINUTES * 60))

    @staticmethod
    async def _delete_after_delay(file_path: str, seconds: int):
        await asyncio.sleep(seconds)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Temporary audio memory flushed successfully: {file_path}")
        except Exception as e:
            logger.error(f"Failed to flush memory for temporary trace {file_path}: {e}")
