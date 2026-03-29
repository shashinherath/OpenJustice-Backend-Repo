"""JWT creation and validation utilities."""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from jose import jwt, JWTError, ExpiredSignatureError, JWTClaimsError

from app.config import settings
from app.core.exceptions import AuthenticationError


class JWTHandler:
    """Secure JWT token management."""

    def __init__(self) -> None:
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.issuer = settings.JWT_ISSUER
        self.audience = settings.JWT_AUDIENCE
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

        if len(self.secret_key) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")

    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create a signed JWT access token."""
        to_encode = data.copy()

        now = datetime.now(timezone.utc)
        expire = (
            now + expires_delta
            if expires_delta
            else now + timedelta(minutes=self.access_token_expire_minutes)
        )

        to_encode.update(
            {
                "iat": now,
                "exp": expire,
                "iss": self.issuer,
                "aud": self.audience,
            }
        )

        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                audience=self.audience,
                issuer=self.issuer,
            )
            return payload
        except ExpiredSignatureError as exc:
            raise AuthenticationError("Token has expired") from exc
        except JWTClaimsError as exc:
            raise AuthenticationError("Invalid token claims") from exc
        except JWTError as exc:
            raise AuthenticationError("Could not validate credentials") from exc


jwt_handler = JWTHandler()
