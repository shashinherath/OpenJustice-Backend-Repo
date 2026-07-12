import httpx
import logging
from typing import Optional
from app.domain.interfaces.recaptcha_verifier import IRecaptchaVerifier

logger = logging.getLogger(__name__)

class GoogleRecaptchaVerifier(IRecaptchaVerifier):
    """Verifies reCAPTCHA tokens with Google's API."""
    
    VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"

    def __init__(self, secret_key: str, min_score: float = 0.5):
        self.secret_key = secret_key
        self.min_score = min_score

    async def verify(self, token: str, ip_address: Optional[str] = None) -> bool:
        """
        Verify a reCAPTCHA v3 token.
        Returns True if successful and score >= min_score, False otherwise.
        """
        if not self.secret_key:
            # If no secret key is configured, bypass verification
            return True

        if not token:
            logger.warning("No reCAPTCHA token provided")
            return False

        data = {
            "secret": self.secret_key,
            "response": token
        }
        
        if ip_address:
            data["remoteip"] = ip_address

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.VERIFY_URL, data=data, timeout=5.0)
                response.raise_for_status()
                
                result = response.json()
                
                if not result.get("success", False):
                    logger.warning(f"reCAPTCHA verification failed: {result.get('error-codes', [])}")
                    return False
                    
                score = result.get("score", 0.0)
                if score < self.min_score:
                    logger.warning(f"reCAPTCHA score {score} is below minimum {self.min_score}")
                    return False
                    
                return True
                
        except Exception as e:
            logger.error(f"Error communicating with reCAPTCHA API: {e}")
            # Depending on policy, we might want to return False or True on API failure.
            # Returning False to be strictly secure.
            return False
