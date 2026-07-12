"""Authentication API controller."""
from fastapi import APIRouter, Depends, Response, Request, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.application.dtos.auth_dto import LoginDto, RegisterDto, LogoutDto, VerifyEmailDto, ResendVerificationDto
from app.application.dtos.user_dto import (
    GetProfileDto,
    UpdateProfileDto,
    ChangePasswordDto,
)
from app.application.services.auth_service import AuthService
from app.application.services.user_service import UserService
from app.config import settings
from app.infrastructure.db.base import get_db
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.security.jwt_handler import jwt_handler
from app.infrastructure.security.password_hasher import BcryptPasswordHasher
from app.infrastructure.repositories.pg_user_session_repository import PgUserSessionRepository
from app.infrastructure.repositories.pg_audit_log_repository import PgAuditLogRepository
from app.infrastructure.repositories.system_settings_repository import SystemSettingsRepository
from app.infrastructure.security.recaptcha_verifier import GoogleRecaptchaVerifier
from app.presentation.schemas.auth_schema import (
    LoginRequest,
    LoginResponseData,
    RegisterRequest,
    RegisterResponseData,
    VerifyEmailRequest,
    ResendVerificationRequest,
)
from app.presentation.schemas.user_schema import (
    UserProfileResponse,
    UserProfileUpdateRequest,
    ChangePasswordRequest,
)
from app.presentation.schemas.response_schema import SuccessResponse
from app.domain.exceptions import InvalidCredentialsError, UserAlreadyExistsError
from app.infrastructure.external.azure_email_client import AzureEmailClient


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=SuccessResponse[LoginResponseData],
    status_code=status.HTTP_200_OK,
)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[LoginResponseData]:
    """Authenticate a user and set an access token cookie."""
    auth_service = AuthService(
        repository=UserRepository(db),
        password_hasher=BcryptPasswordHasher(),
        token_issuer=jwt_handler,
        user_session_repo=PgUserSessionRepository(db),
        audit_log_repo=PgAuditLogRepository(db),
        system_settings_repo=SystemSettingsRepository(db),
        recaptcha_verifier=GoogleRecaptchaVerifier(secret_key=settings.RECAPTCHA_SECRET_KEY) if settings.RECAPTCHA_SECRET_KEY else None,
    )

    result = await auth_service.login(
        LoginDto(
            email=payload.email,
            phone_number=payload.phone_number,
            password=payload.password,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            channel="web",
            recaptcha_token=payload.recaptcha_token,
        )
    )

    system_settings_repo = SystemSettingsRepository(db)
    sys_settings = await system_settings_repo.get_settings()
    jwt_expiry_minutes = sys_settings.jwt_expiry_minutes if sys_settings else settings.ACCESS_TOKEN_EXPIRE_MINUTES

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
        max_age=jwt_expiry_minutes * 60,
        path="/",
    )

    data = LoginResponseData(
        uuid=result.uuid,
        first_name=result.first_name,
        last_name=result.last_name,
        role=result.role,
        preferred_language=result.preferred_language,
        access_token=result.access_token,
    )

    return SuccessResponse(data=data, message="Login successful")


@router.post(
    "/register",
    response_model=SuccessResponse[RegisterResponseData],
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[RegisterResponseData]:
    """Register a new user (requires email verification)."""
    service = AuthService(
        repository=UserRepository(db),
        password_hasher=BcryptPasswordHasher(),
        token_issuer=jwt_handler,
        audit_log_repo=PgAuditLogRepository(db),
        recaptcha_verifier=GoogleRecaptchaVerifier(secret_key=settings.RECAPTCHA_SECRET_KEY) if settings.RECAPTCHA_SECRET_KEY else None,
        email_client=AzureEmailClient(),
    )
    result = await service.register(
        RegisterDto(
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            phone_number=payload.phone_number,
            password=payload.password,
            preferred_language=payload.preferred_language,
            recaptcha_token=payload.recaptcha_token,
            ip_address=request.client.host if request.client else None,
        )
    )

    data = RegisterResponseData(
        uuid=result.uuid,
        first_name=result.first_name,
        last_name=result.last_name,
        role=result.role,
        preferred_language=result.preferred_language,
    )

    return SuccessResponse(data=data, message="Registration successful. Please check your email to verify your account.")


@router.post(
    "/verify-email",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_200_OK,
)
async def verify_email(
    payload: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[dict]:
    """Verify user's email."""
    service = AuthService(
        repository=UserRepository(db),
        password_hasher=BcryptPasswordHasher(),
        token_issuer=jwt_handler,
    )
    
    try:
        await service.verify_email(VerifyEmailDto(token=payload.token))
        return SuccessResponse(data={}, message="Email verified successfully")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/resend-verification",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_200_OK,
)
async def resend_verification(
    payload: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[dict]:
    """Resend email verification link."""
    service = AuthService(
        repository=UserRepository(db),
        password_hasher=BcryptPasswordHasher(),
        token_issuer=jwt_handler,
        email_client=AzureEmailClient(),
    )
    
    try:
        await service.resend_verification_email(ResendVerificationDto(email=payload.email))
        # Always return success to prevent email enumeration
        return SuccessResponse(data={}, message="If your email is registered, a verification link has been sent.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.post(
    "/logout",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_200_OK,
)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[dict]:
    """Log out a user and clear the authentication cookie."""
    # Extract user ID from the JWT payload injected by middleware
    user_data = getattr(request.state, "user", None)
    if not user_data or "sub" not in user_data:
        raise Exception("Not authenticated")
    
    user_id = UUID(user_data["sub"])
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    service = AuthService(
        repository=UserRepository(db),
        password_hasher=BcryptPasswordHasher(),
        token_issuer=jwt_handler,
        audit_log_repo=PgAuditLogRepository(db),
    )
    
    await service.logout(
        LogoutDto(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            channel="web",
        )
    )

    # Clear the authentication cookie
    cookie_secure = (
        settings.AUTH_COOKIE_SECURE
        if settings.AUTH_COOKIE_SECURE is not None
        else not settings.DEBUG
    )
    
    response.delete_cookie(
        key=settings.AUTH_COOKIE_NAME,
        secure=cookie_secure,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path="/",
    )

    return SuccessResponse(data={}, message="Logout successful")


@router.get(
    "/me",
    response_model=SuccessResponse[UserProfileResponse],
    status_code=status.HTTP_200_OK,
)
async def get_current_user_profile(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[UserProfileResponse]:
    """Get current authenticated user's profile."""
    user_data = getattr(request.state, "user", None)
    if not user_data or "sub" not in user_data:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = UUID(user_data["sub"])

    service = UserService(
        repository=UserRepository(db),
        password_hasher=BcryptPasswordHasher(),
    )

    try:
        profile = await service.get_profile(GetProfileDto(user_id=user_id))
        return SuccessResponse(data=profile, message="Profile retrieved successfully")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch(
    "/users/me",
    response_model=SuccessResponse[UserProfileResponse],
    status_code=status.HTTP_200_OK,
)
async def update_current_user_profile(
    payload: UserProfileUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[UserProfileResponse]:
    """Update current authenticated user's profile."""
    user_data = getattr(request.state, "user", None)
    if not user_data or "sub" not in user_data:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = UUID(user_data["sub"])

    service = UserService(
        repository=UserRepository(db),
        password_hasher=BcryptPasswordHasher(),
    )

    try:
        updated_profile = await service.update_profile(
            UpdateProfileDto(
                user_id=user_id,
                first_name=payload.first_name,
                last_name=payload.last_name,
                email=payload.email,
                preferred_language=payload.preferred_language,
                avatar_url=payload.avatar_url,
            )
        )
        return SuccessResponse(
            data=updated_profile, message="Profile updated successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/change-password",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_200_OK,
)
async def change_user_password(
    payload: ChangePasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[dict]:
    """Change current authenticated user's password."""
    user_data = getattr(request.state, "user", None)
    if not user_data or "sub" not in user_data:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = UUID(user_data["sub"])

    service = UserService(
        repository=UserRepository(db),
        password_hasher=BcryptPasswordHasher(),
    )

    try:
        await service.change_password(
            ChangePasswordDto(
                user_id=user_id,
                current_password=payload.current_password,
                new_password=payload.new_password,
            )
        )
        return SuccessResponse(data={}, message="Password changed successfully")
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
