"""Authentication API controller."""
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.auth_dto import LoginDto
from app.application.services.auth_service import AuthService
from app.config import settings
from app.infrastructure.db.base import get_db
from app.presentation.schemas.auth_schema import LoginRequest, LoginResponseData
from app.presentation.schemas.response_schema import SuccessResponse


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=SuccessResponse[LoginResponseData],
    status_code=status.HTTP_200_OK,
)
async def login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[LoginResponseData]:
    """Authenticate a user and set an access token cookie."""
    service = AuthService(db=db)
    result = await service.login(
        LoginDto(
            email=payload.email,
            phone_number=payload.phone_number,
            password=payload.password,
        )
    )

    cookie_secure = (
        settings.AUTH_COOKIE_SECURE
        if settings.AUTH_COOKIE_SECURE is not None
        else not settings.DEBUG
    )

    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=result.access_token,
        httponly=True,
        secure=cookie_secure,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    data = LoginResponseData(
        uuid=result.uuid,
        role=result.role,
        preferred_language=result.preferred_language,
    )

    return SuccessResponse(data=data, message="Login successful")
