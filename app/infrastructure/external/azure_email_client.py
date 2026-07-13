"""Azure Communication Services Email Client."""
import logging
from azure.communication.email.aio import EmailClient
from app.domain.interfaces.email_client import IEmailClient
from app.config import settings

logger = logging.getLogger(__name__)


class AzureEmailClient(IEmailClient):
    """Email client implementation using Azure Communication Services."""

    def __init__(self, connection_string: str = None, sender_email: str = None):
        """Initialize the Azure Email Client.
        
        Args:
            connection_string: The Azure Communication Services connection string.
            sender_email: The 'From' email address configured in Azure.
        """
        self.connection_string = connection_string or settings.AZURE_COMMUNICATION_CONNECTION_STRING
        self.sender_email = sender_email or getattr(settings, "AZURE_SENDER_EMAIL", "donotreply@openjustice.com")
        self.client = None
        
        if self.connection_string:
            try:
                self.client = EmailClient.from_connection_string(self.connection_string)
            except Exception as e:
                logger.error(f"Failed to initialize Azure Email Client: {str(e)}")

    async def send_verification_email(self, to_email: str, token: str) -> bool:
        """Send an email verification link to the user."""
        if not self.client:
            logger.warning("Azure Email Client is not configured. Simulating email sending.")
            logger.info(f"SIMULATED EMAIL TO {to_email}: Verification Token is {token}")
            return True

        verification_url = f"{settings.FRONTEND_BASE_URL}/verify-email?token={token}"
        
        message = {
            "senderAddress": self.sender_email,
            "recipients":  {
                "to": [{"address": to_email}],
            },
            "content": {
                "subject": "Verify your OpenJustice account",
                "plainText": f"Please verify your OpenJustice account by clicking this link: {verification_url}",
                "html": f"""
                <html>
                    <body>
                        <h2>Welcome to OpenJustice!</h2>
                        <p>Please verify your email address by clicking the link below:</p>
                        <p><a href="{verification_url}">Verify Email Address</a></p>
                        <p>Or copy and paste this URL into your browser:</p>
                        <p>{verification_url}</p>
                    </body>
                </html>
                """
            }
        }

        try:
            async with self.client as client:
                poller = await client.begin_send(message)
                result = await poller.result()
                logger.info(f"Verification email sent to {to_email}, message_id: {result.get('messageId')}")
                return True
        except Exception as e:
            logger.error(f"Failed to send verification email to {to_email}: {str(e)}")
            return False
