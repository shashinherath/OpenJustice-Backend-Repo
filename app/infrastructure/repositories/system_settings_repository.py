from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.infrastructure.models.system_settings import SystemSettings

class SystemSettingsRepository:
    """Data access layer for system settings."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_settings(self) -> SystemSettings:
        result = await self.db.execute(select(SystemSettings).limit(1))
        settings = result.scalars().first()
        
        if not settings:
            settings = SystemSettings(
                id=str(uuid.uuid4()),
                enabled_languages=["en", "si", "ta"],
                default_language="en",
                translation_pipeline_enabled=True
            )
            self.db.add(settings)
            await self.db.flush()
            await self.db.refresh(settings)
            
        return settings

    async def update_settings(self, enabled_languages: list[str], default_language: str, translation_pipeline_enabled: bool) -> SystemSettings:
        settings = await self.get_settings()
        
        settings.enabled_languages = enabled_languages
        settings.default_language = default_language
        settings.translation_pipeline_enabled = translation_pipeline_enabled
        
        await self.db.commit()
        await self.db.refresh(settings)
        return settings
