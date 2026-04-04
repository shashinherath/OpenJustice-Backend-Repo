import logging

from app.domain.interfaces.whatsapp_client import IWhatsAppClient

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service to handle WhatsApp messaging logic."""

    def __init__(self, whatsapp_client: IWhatsAppClient):
        self.whatsapp_client = whatsapp_client

    async def handle_incoming_message(self, from_number: str, body: str) -> None:
        """
        Process an incoming WhatsApp message.
        
        For now, this function just echoes an acknowledgment back to the user.
        Eventually, it will integrate with the LLM or RagService to generate responses.
        
        Args:
            from_number: The sender's WhatsApp number.
            body: The text of the message.
        """
        logger.info(f"Received WhatsApp message from {from_number}: {body}")
        
        # Simple echo/acknowledgment
        reply_message = f"OpenJustice Backend received your message: '{body}'. We will process it shortly."
        
        try:
            await self.whatsapp_client.send_message(
                to=from_number,
                body=reply_message
            )
        except Exception as e:
            logger.error(f"Failed to send acknowledgment to {from_number}: {e}")
            # We don't necessarily raise here to avoid Twilio retrying and potentially
            # causing spam, or we can raise depending on the desired error handling strategy.
