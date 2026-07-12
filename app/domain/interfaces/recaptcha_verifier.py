from abc import ABC, abstractmethod
from typing import Optional


class IRecaptchaVerifier(ABC):
    """Interface for verifying reCAPTCHA tokens."""

    @abstractmethod
    async def verify(self, token: str, ip_address: Optional[str] = None) -> bool:
        """
        Verify a reCAPTCHA token.

        Args:
            token (str): The reCAPTCHA token provided by the client.
            ip_address (str, optional): The user's IP address.

        Returns:
            bool: True if the token is valid, False otherwise.
        """
        pass
