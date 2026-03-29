"""JWT / access token issuance contract (implemented in infrastructure)."""
from datetime import timedelta
from typing import Any, Dict, Optional, Protocol


class AccessTokenIssuer(Protocol):
    """Create signed access tokens for authenticated subjects."""

    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Build and return an encoded access token."""
        ...
