import logging
from twilio.rest import Client
import asyncio

from app.config import settings
from app.domain.interfaces.whatsapp_client import IWhatsAppClient

logger = logging.getLogger(__name__)


class TwilioWhatsAppClient(IWhatsAppClient):
    """Twilio implementation of the WhatsApp client."""

    def __init__(self):
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
            logger.warning("Twilio credentials not fully configured.")
            # We initialize without credentials for cases where the app handles missing env gracefully
            # but ideally, this should raise an infrastructure exception or fail fast.
            # Allowing it to pass so tests or dev can start without breaking.
            self.client = None
        else:
            self.client = Client(
                settings.TWILIO_ACCOUNT_SID, 
                settings.TWILIO_AUTH_TOKEN
            )
        self.from_number = settings.TWILIO_WHATSAPP_NUMBER or ""

    async def send_message(self, to: str, body: str) -> None:
        """Sends a WhatsApp message via Twilio async API."""
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

            await asyncio.to_thread(
                self.client.messages.create,
                body=body,
                from_=from_num,
                to=to
            )
            logger.info(f"WhatsApp message sent to {to}")
        except Exception as e:
            logger.error(f"Failed to send Twilio message to {to}: {e}")
            raise
