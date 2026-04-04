"""WhatsApp client interface."""
from abc import ABC, abstractmethod


class IWhatsAppClient(ABC):
    """Interface for external WhatsApp messaging providers."""

    @abstractmethod
    async def send_message(self, to: str, body: str) -> None:
        """
        Send a WhatsApp message.
        
        Args:
            to: The recipient's WhatsApp number (e.g., 'whatsapp:+1234567890')
            body: The text content of the message
        """
        pass
