"""Authentication middleware for processing JWT tokens."""
from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.infrastructure.security.jwt_handler import jwt_handler
from app.presentation.schemas.response_schema import ErrorDetail, ErrorResponse

# Endpoints that bypass authentication
PUBLIC_PATHS = [
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/auth/login",
    "/api/auth/register",
    "/api/whatsapp/webhook",
    "/health",
]


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for decoding JWT tokens and authenticating requests."""

    async def dispatch(self, request: Request, call_next: Callable):
        # Allow CORS preflight requests
        if request.method == "OPTIONS":
            return await call_next(request)

        # Allow public paths
        if any(request.url.path.startswith(path) for path in PUBLIC_PATHS):
            return await call_next(request)

        # Extract token from header or cookie
        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

        if not token and settings.AUTH_COOKIE_NAME:
            token = request.cookies.get(settings.AUTH_COOKIE_NAME)

        # Return 401 if no token found
        if not token:
            content = ErrorResponse(
                error=ErrorDetail(
                    code="UNAUTHORIZED",
                    message="Authentication credentials were not provided.",
                )
            ).model_dump(mode="json")
            return JSONResponse(status_code=401, content=content)

        # Validate token and inject payload
        try:
            payload = jwt_handler.verify_token(token)
            request.state.user = payload
        except Exception as e:
            content = ErrorResponse(
                error=ErrorDetail(
                    code="INVALID_TOKEN",
                    message=f"Token validation failed: {str(e)}",
                )
            ).model_dump(mode="json")
            return JSONResponse(status_code=401, content=content)

        # Proceed to route
        response = await call_next(request)
        return response
