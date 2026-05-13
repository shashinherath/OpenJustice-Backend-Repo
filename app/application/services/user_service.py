"""User service for profile management."""
from app.application.dtos.user_dto import (
    GetProfileDto,
    UpdateProfileDto,
    ChangePasswordDto,
)
from app.domain.exceptions import InvalidCredentialsError
from app.domain.interfaces.password_hasher import PasswordHasher
from app.domain.interfaces.user_repository import IUserRepository
from app.presentation.schemas.user_schema import UserProfileResponse


class UserService:
    """Business logic for user profile management."""

    def __init__(
        self,
        repository: IUserRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self.repository = repository
        self.password_hasher = password_hasher

    async def get_profile(self, dto: GetProfileDto) -> UserProfileResponse:
        """Retrieve user profile."""
        user = await self.repository.get_by_uuid(dto.user_id)
        if not user:
            raise ValueError(f"User with ID {dto.user_id} not found")

        return UserProfileResponse(
            uuid=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            role=user.role,
            preferred_language=user.preferred_language,
            avatar_url=user.avatar_url,
        )

    async def update_profile(self, dto: UpdateProfileDto) -> UserProfileResponse:
        """Update user profile information."""
        updated_user = await self.repository.update_profile(
            user_id=dto.user_id,
            first_name=dto.first_name,
            last_name=dto.last_name,
            email=dto.email,
            preferred_language=dto.preferred_language,
            avatar_url=dto.avatar_url,
        )

        if not updated_user:
            raise ValueError(f"User with ID {dto.user_id} not found")

        return UserProfileResponse(
            uuid=updated_user.id,
            first_name=updated_user.first_name,
            last_name=updated_user.last_name,
            email=updated_user.email,
            role=updated_user.role,
            preferred_language=updated_user.preferred_language,
            avatar_url=updated_user.avatar_url,
        )

    async def change_password(self, dto: ChangePasswordDto) -> None:
        """Change user password."""
        user = await self.repository.get_by_uuid(dto.user_id)
        if not user or not user.hashed_password:
            raise ValueError(f"User with ID {dto.user_id} not found")

        # Verify current password
        if not self.password_hasher.verify_password(
            dto.current_password, user.hashed_password
        ):
            raise InvalidCredentialsError("Current password is incorrect")

        # Hash new password
        hashed_new_password = self.password_hasher.hash_password(dto.new_password)

        # Update password
        await self.repository.set_password(dto.user_id, hashed_new_password)
