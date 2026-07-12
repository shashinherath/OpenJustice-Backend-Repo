"""Email client interface."""
from abc import ABC, abstractmethod


class IEmailClient(ABC):
    """Abstract interface for sending emails."""

    @abstractmethod
    async def send_verification_email(self, to_email: str, token: str) -> bool:
        """Send an email verification link to the user.
        
        Args:
            to_email: The recipient's email address.
            token: The verification token.
            
        Returns:
            bool: True if the email was sent successfully, False otherwise.
        """
        pass
