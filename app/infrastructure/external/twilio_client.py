import logging
from twilio.rest import Client
import asyncio

from app.config import settings
from app.domain.interfaces.whatsapp_client import IWhatsAppClient

logger = logging.getLogger(__name__)


from app.infrastructure.repositories.system_settings_repository import SystemSettingsRepository

class TwilioWhatsAppClient(IWhatsAppClient):
    """Twilio implementation of the WhatsApp client."""

    def __init__(self, system_settings_repository: SystemSettingsRepository = None):
        self.system_settings_repository = system_settings_repository
        self.client = None
        self.from_number = ""
        self.current_sid = None
        self.current_token = None
        
        # Initial setup from env
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            self.current_sid = settings.TWILIO_ACCOUNT_SID
            self.current_token = settings.TWILIO_AUTH_TOKEN
            self.from_number = settings.TWILIO_WHATSAPP_NUMBER or ""
        else:
            logger.warning("Twilio credentials not fully configured in env.")

    async def _ensure_client(self):
        if self.system_settings_repository:
            sys_settings = await self.system_settings_repository.get_settings()
            db_sid = sys_settings.twilio_account_sid
            db_token = sys_settings.twilio_auth_token
            db_phone = sys_settings.whatsapp_phone_number
            
            if db_sid and db_token:
                if db_sid != self.current_sid or db_token != self.current_token:
                    self.current_sid = db_sid
                    self.current_token = db_token
                    self.client = Client(db_sid, db_token)
            
            if db_phone and db_phone != self.from_number:
                self.from_number = db_phone

    async def send_message(self, to: str, body: str = None, media_url: str = None) -> None:
        """Sends a WhatsApp message via Twilio async API natively handling media streams."""
        await self._ensure_client()
        
        if not self.client:
            logger.error("Twilio client is not initialized. Cannot send message.")
            return

        try:
            # Twilio sandbox requires numbers in format 'whatsapp:+1234567890'
            if not to.startswith("whatsapp:"):
                to = f"whatsapp:{to}"
                
            from_num = self.from_number
            if not from_num.startswith("whatsapp:"):
                from_num = f"whatsapp:{from_num}"

            # Setup kwargs so we can bounce either text or media dynamically
            kwargs = {"from_": from_num, "to": to}
            if body:
                kwargs["body"] = body
            if media_url:
                # Twilio native accepts lists of media_urls!
                kwargs["media_url"] = [media_url]

            await asyncio.to_thread(self.client.messages.create, **kwargs)
            logger.info(f"WhatsApp message/audio sent to {to}")
        except Exception as e:
            logger.error(f"Failed to send Twilio message to {to}: {e}")
            raise
