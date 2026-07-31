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

    async def update_ai_settings(self, ai_model_name: str, ai_temperature: float, ai_max_tokens: int, ai_top_p: float, ai_frequency_penalty: float) -> SystemSettings:
        settings = await self.get_settings()
        
        settings.ai_model_name = ai_model_name
        settings.ai_temperature = ai_temperature
        settings.ai_max_tokens = ai_max_tokens
        settings.ai_top_p = ai_top_p
        settings.ai_frequency_penalty = ai_frequency_penalty
        
        await self.db.commit()
        await self.db.refresh(settings)
        return settings

    async def update_retrieval_settings(
        self,
        retrieval_top_k: int,
        retrieval_similarity_threshold: float,
        retrieval_embedding_model: str,
        retrieval_chunk_size: int,
        retrieval_chunk_overlap: int,
        semantic_cache_ttl_hours: int = 0
    ) -> SystemSettings:
        settings = await self.get_settings()

        settings.retrieval_top_k = retrieval_top_k
        settings.retrieval_similarity_threshold = retrieval_similarity_threshold
        settings.retrieval_embedding_model = retrieval_embedding_model
        settings.retrieval_chunk_size = retrieval_chunk_size
        settings.retrieval_chunk_overlap = retrieval_chunk_overlap
        settings.semantic_cache_ttl_hours = semantic_cache_ttl_hours

        await self.db.commit()
        await self.db.refresh(settings)
        return settings

    async def update_integration_settings(
        self,
        openai_api_key: Optional[str],
        twilio_account_sid: Optional[str],
        twilio_auth_token: Optional[str],
        whatsapp_phone_number: Optional[str],
        web_socket_url: Optional[str]
    ) -> SystemSettings:
        settings = await self.get_settings()
        
        if openai_api_key is not None:
            settings.openai_api_key = openai_api_key
        if twilio_account_sid is not None:
            settings.twilio_account_sid = twilio_account_sid
        if twilio_auth_token is not None:
            settings.twilio_auth_token = twilio_auth_token
        if whatsapp_phone_number is not None:
            settings.whatsapp_phone_number = whatsapp_phone_number
        if web_socket_url is not None:
            settings.web_socket_url = web_socket_url
            
        await self.db.commit()
        await self.db.refresh(settings)
        return settings

    async def update_security_settings(
        self,
        jwt_expiry_minutes: int,
        rate_limit_per_minute: int,
        prompt_validation_enabled: bool,
        account_lockout_threshold: int
    ) -> SystemSettings:
        settings = await self.get_settings()
        
        settings.jwt_expiry_minutes = jwt_expiry_minutes
        settings.rate_limit_per_minute = rate_limit_per_minute
        settings.prompt_validation_enabled = prompt_validation_enabled
        settings.account_lockout_threshold = account_lockout_threshold
        
        await self.db.commit()
        await self.db.refresh(settings)
        return settings
