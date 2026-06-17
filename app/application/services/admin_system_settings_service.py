from app.infrastructure.repositories.system_settings_repository import SystemSettingsRepository
from app.infrastructure.models.system_settings import SystemSettings

class AdminSystemSettingsService:
    """Service for managing system-wide settings."""

    def __init__(self, settings_repository: SystemSettingsRepository):
        self.settings_repository = settings_repository

    async def get_language_settings(self) -> SystemSettings:
        return await self.settings_repository.get_settings()

    async def update_language_settings(self, enabled_languages: list[str], default_language: str, translation_pipeline_enabled: bool) -> SystemSettings:
        return await self.settings_repository.update_settings(
            enabled_languages=enabled_languages,
            default_language=default_language,
            translation_pipeline_enabled=translation_pipeline_enabled
        )
