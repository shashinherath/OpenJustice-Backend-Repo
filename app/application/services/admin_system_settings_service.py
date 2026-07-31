from app.infrastructure.repositories.system_settings_repository import SystemSettingsRepository
from app.infrastructure.models.system_settings import SystemSettings
from app.domain.interfaces.audit_log_repository import IAuditLogRepository

class AdminSystemSettingsService:
    """Service for managing system-wide settings."""

    def __init__(self, settings_repository: SystemSettingsRepository, audit_log_repo: IAuditLogRepository = None):
        self.settings_repository = settings_repository
        self.audit_log_repo = audit_log_repo

    async def get_language_settings(self) -> SystemSettings:
        return await self.settings_repository.get_settings()

    async def update_language_settings(self, enabled_languages: list[str], default_language: str, translation_pipeline_enabled: bool, current_user_id: str = None) -> SystemSettings:
        settings = await self.settings_repository.update_settings(
            enabled_languages=enabled_languages,
            default_language=default_language,
            translation_pipeline_enabled=translation_pipeline_enabled
        )
        if self.audit_log_repo:
            from uuid import UUID
            await self.audit_log_repo.log_action(
                user_id=UUID(current_user_id) if current_user_id else None,
                action="UPDATE_LANGUAGE_SETTINGS",
                entity="SystemSettings",
                metadata={"default_language": default_language}
            )
        return settings

    async def get_ai_settings(self) -> SystemSettings:
        return await self.settings_repository.get_settings()

    async def update_ai_settings(self, ai_model_name: str, ai_temperature: float, ai_max_tokens: int, ai_top_p: float, ai_frequency_penalty: float, current_user_id: str = None) -> SystemSettings:
        settings = await self.settings_repository.update_ai_settings(
            ai_model_name=ai_model_name,
            ai_temperature=ai_temperature,
            ai_max_tokens=ai_max_tokens,
            ai_top_p=ai_top_p,
            ai_frequency_penalty=ai_frequency_penalty
        )
        if self.audit_log_repo:
            from uuid import UUID
            await self.audit_log_repo.log_action(
                user_id=UUID(current_user_id) if current_user_id else None,
                action="UPDATE_AI_SETTINGS",
                entity="SystemSettings",
                metadata={"ai_model_name": ai_model_name}
            )
        return settings

    async def get_retrieval_settings(self) -> SystemSettings:
        return await self.settings_repository.get_settings()

    async def update_retrieval_settings(
        self,
        retrieval_top_k: int,
        retrieval_similarity_threshold: float,
        retrieval_embedding_model: str,
        retrieval_chunk_size: int,
        retrieval_chunk_overlap: int,
        semantic_cache_ttl_hours: int = 0,
        current_user_id: str = None
    ) -> SystemSettings:
        settings = await self.settings_repository.update_retrieval_settings(
            retrieval_top_k=retrieval_top_k,
            retrieval_similarity_threshold=retrieval_similarity_threshold,
            retrieval_embedding_model=retrieval_embedding_model,
            retrieval_chunk_size=retrieval_chunk_size,
            retrieval_chunk_overlap=retrieval_chunk_overlap,
            semantic_cache_ttl_hours=semantic_cache_ttl_hours
        )
        if self.audit_log_repo:
            from uuid import UUID
            await self.audit_log_repo.log_action(
                user_id=UUID(current_user_id) if current_user_id else None,
                action="UPDATE_RETRIEVAL_SETTINGS",
                entity="SystemSettings",
                metadata={"retrieval_embedding_model": retrieval_embedding_model}
            )
        return settings

    async def get_integration_settings(self) -> SystemSettings:
        return await self.settings_repository.get_settings()

    async def update_integration_settings(
        self,
        openai_api_key: str = None,
        twilio_account_sid: str = None,
        twilio_auth_token: str = None,
        whatsapp_phone_number: str = None,
        web_socket_url: str = None,
        current_user_id: str = None
    ) -> SystemSettings:
        settings = await self.settings_repository.update_integration_settings(
            openai_api_key=openai_api_key,
            twilio_account_sid=twilio_account_sid,
            twilio_auth_token=twilio_auth_token,
            whatsapp_phone_number=whatsapp_phone_number,
            web_socket_url=web_socket_url
        )
        if self.audit_log_repo:
            from uuid import UUID
            await self.audit_log_repo.log_action(
                user_id=UUID(current_user_id) if current_user_id else None,
                action="UPDATE_INTEGRATION_SETTINGS",
                entity="SystemSettings",
                metadata={"whatsapp_phone_number_updated": bool(whatsapp_phone_number)}
            )
        return settings

    async def get_security_settings(self) -> SystemSettings:
        return await self.settings_repository.get_settings()

    async def update_security_settings(
        self,
        jwt_expiry_minutes: int,
        rate_limit_per_minute: int,
        prompt_validation_enabled: bool,
        account_lockout_threshold: int,
        current_user_id: str = None
    ) -> SystemSettings:
        settings = await self.settings_repository.update_security_settings(
            jwt_expiry_minutes=jwt_expiry_minutes,
            rate_limit_per_minute=rate_limit_per_minute,
            prompt_validation_enabled=prompt_validation_enabled,
            account_lockout_threshold=account_lockout_threshold
        )
        if self.audit_log_repo:
            from uuid import UUID
            await self.audit_log_repo.log_action(
                user_id=UUID(current_user_id) if current_user_id else None,
                action="UPDATE_SECURITY_SETTINGS",
                entity="SystemSettings",
                metadata={"prompt_validation_enabled": prompt_validation_enabled}
            )
        return settings
