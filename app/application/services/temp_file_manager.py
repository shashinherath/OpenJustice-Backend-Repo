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
    async def save_upload_file(upload_file) -> str:
        """Save a FastAPI UploadFile to the local temp directory for processing."""
        os.makedirs(settings.AUDIO_TEMP_DIR, exist_ok=True)
        
        # Get extension if exists
        ext = ".webm"
        if upload_file.filename and "." in upload_file.filename:
            ext = f".{upload_file.filename.split('.')[-1]}"
            
        filename = f"web_in_{uuid.uuid4()}{ext}"
        file_path = os.path.join(settings.AUDIO_TEMP_DIR, filename)
        
        try:
            content = await upload_file.read()
            def _write_file():
                with open(file_path, 'wb') as f:
                    f.write(content)
            
            await asyncio.to_thread(_write_file)
            
            logger.info(f"Successfully saved uploaded audio to {file_path}")
            TempFileManager.schedule_deletion(file_path)
            return file_path
        except Exception as e:
            logger.error(f"Failed to save uploaded audio: {e}", exc_info=True)
            raise ValueError(f"Error saving incoming voice note: {e}")

    @staticmethod
    async def download_twilio_audio(media_url: str, twilio_sid: str = None, twilio_token: str = None) -> str:
        """Download remote Twilio mobile audio block internally for local Whisper consumption."""
        os.makedirs(settings.AUDIO_TEMP_DIR, exist_ok=True)
        
        # Twilio whatsapp audio usually comes back as OGG files by default.
        filename = f"twilio_in_{uuid.uuid4()}.ogg"
        file_path = os.path.join(settings.AUDIO_TEMP_DIR, filename)

        try:
            # Twilio media usually requires HTTP Basic Auth with Account SID and Auth Token 
            # if "Secure Media" is explicitly enabled, otherwise it serves publicly on hard unguessable URLs.
            auth = None
            
            sid = twilio_sid or settings.TWILIO_ACCOUNT_SID
            token = twilio_token or settings.TWILIO_AUTH_TOKEN
            
            if sid and token:
                auth = (sid, token)
                
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
