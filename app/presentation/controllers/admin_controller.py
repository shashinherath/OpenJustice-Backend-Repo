from fastapi import APIRouter, Depends, Request, status, HTTPException, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.base import get_db
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.repositories.chat_repository import ChatRepository
from app.infrastructure.repositories.document_repository import DocumentRepository
from app.infrastructure.repositories.pg_llm_log_repository import PgLLMLogRepository
from app.infrastructure.repositories.pg_audit_log_repository import PgAuditLogRepository

from app.application.services.admin_overview_service import AdminOverviewService
from app.application.services.admin_users_service import AdminUsersService
from app.application.services.admin_knowledge_service import AdminKnowledgeService
from app.application.services.admin_logs_service import AdminLogsService
from app.application.services.admin_retrieval_service import AdminRetrievalService
from app.application.services.admin_platform_analytics_service import AdminPlatformAnalyticsService
from app.application.services.admin_usage_analytics_service import AdminUsageAnalyticsService
from app.application.services.admin_cost_analytics_service import AdminCostAnalyticsService
from app.application.services.admin_multilingual_analytics_service import AdminMultilingualAnalyticsService

from app.presentation.schemas.admin_schema import (
    AdminOverviewResponse, AdminUserListResponse, AdminUserStatusUpdate, AdminUserItem,
    AdminKnowledgeResponse, AdminRetrievalMonitoringResponse,
    AdminLogListResponse, AdminLogStatusUpdate,
    AdminPlatformAnalyticsResponse, AdminUsageAnalyticsResponse,
    AdminCostAnalyticsResponse, AdminMultilingualAnalyticsResponse,
    SecuritySettingsResponse, SecuritySettingsUpdate
)

router = APIRouter(prefix="/admin", tags=["Admin"])

def get_admin_overview_service(db: AsyncSession = Depends(get_db)) -> AdminOverviewService:
    return AdminOverviewService(UserRepository(db), ChatRepository(db), DocumentRepository(db), PgLLMLogRepository(db), PgAuditLogRepository(db))

def get_admin_users_service(db: AsyncSession = Depends(get_db)) -> AdminUsersService:
    from app.infrastructure.security.password_hasher import BcryptPasswordHasher
    return AdminUsersService(UserRepository(db), password_hasher=BcryptPasswordHasher(), audit_log_repo=PgAuditLogRepository(db))

def get_admin_knowledge_service(db: AsyncSession = Depends(get_db)) -> AdminKnowledgeService:
    return AdminKnowledgeService(DocumentRepository(db))

def get_admin_logs_service(db: AsyncSession = Depends(get_db)) -> AdminLogsService:
    from app.infrastructure.repositories.pg_audio_log_repository import PgAudioLogRepository
    from app.infrastructure.repositories.pg_retrieval_log_repository import PgRetrievalLogRepository
    return AdminLogsService(
        PgLLMLogRepository(db),
        PgAudioLogRepository(db),
        PgRetrievalLogRepository(db)
    )

def get_admin_retrieval_service(db: AsyncSession = Depends(get_db)) -> AdminRetrievalService:
    from app.infrastructure.repositories.system_settings_repository import SystemSettingsRepository
    return AdminRetrievalService(DocumentRepository(db), system_settings_repo=SystemSettingsRepository(db))

def get_admin_platform_analytics_service(db: AsyncSession = Depends(get_db)) -> AdminPlatformAnalyticsService:
    return AdminPlatformAnalyticsService(ChatRepository(db))

def get_admin_usage_analytics_service(db: AsyncSession = Depends(get_db)) -> AdminUsageAnalyticsService:
    return AdminUsageAnalyticsService(ChatRepository(db), UserRepository(db))

def get_admin_cost_analytics_service(db: AsyncSession = Depends(get_db)) -> AdminCostAnalyticsService:
    return AdminCostAnalyticsService(ChatRepository(db), PgLLMLogRepository(db))

def get_admin_multilingual_analytics_service(db: AsyncSession = Depends(get_db)) -> AdminMultilingualAnalyticsService:
    return AdminMultilingualAnalyticsService(ChatRepository(db))


@router.get("/overview", response_model=AdminOverviewResponse)
async def get_overview(request: Request, service: AdminOverviewService = Depends(get_admin_overview_service)):
    return await service.get_overview_stats()

from app.infrastructure.models.semantic_cache import SemanticCache
from sqlalchemy import delete

@router.post("/clear-semantic-cache")
async def clear_semantic_cache(request: Request, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(SemanticCache))
    await db.commit()
    return {"message": "Semantic cache cleared successfully"}

@router.get("/users", response_model=AdminUserListResponse)
async def list_users(request: Request, skip: int = 0, limit: int = 100, search_query: str | None = None, role: str | None = None, status_filter: str | None = None, service: AdminUsersService = Depends(get_admin_users_service)):
    return await service.get_users(skip=skip, limit=limit, search_query=search_query, role=role, status=status_filter)

from app.presentation.schemas.admin_schema import AdminUserCreateRequest
from app.presentation.schemas.response_schema import SuccessResponse
from app.domain.exceptions import UserAlreadyExistsError

@router.post("/users", response_model=SuccessResponse[AdminUserItem])
async def create_admin_user(request: Request, payload: AdminUserCreateRequest, service: AdminUsersService = Depends(get_admin_users_service)):
    current_user_id = getattr(request.state, "user", {}).get("sub")
    try:
        user = await service.create_admin_user(
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone_number=payload.phone_number,
            email=payload.email,
            password=payload.password,
            current_user_id=current_user_id
        )
        return SuccessResponse(data=AdminUserItem(**user), message="Admin user created successfully")
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/users/{user_id}/status", response_model=AdminUserItem)
async def update_user_status(user_id: str, status_update: AdminUserStatusUpdate, request: Request, service: AdminUsersService = Depends(get_admin_users_service)):
    current_user_id = getattr(request.state, "user", {}).get("sub")
    try:
        return await service.update_user_status(user_id, status_update.is_active, current_user_id=current_user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/retrieval-monitoring", response_model=AdminRetrievalMonitoringResponse)
async def get_retrieval_monitoring(request: Request, service: AdminRetrievalService = Depends(get_admin_retrieval_service)):
    return await service.get_retrieval_monitoring()

@router.get("/knowledge", response_model=AdminKnowledgeResponse)
async def get_knowledge(request: Request, service: AdminKnowledgeService = Depends(get_admin_knowledge_service)):
    return await service.get_knowledge_metrics()

@router.get("/logs", response_model=AdminLogListResponse)
async def get_logs(request: Request, skip: int = 0, limit: int = 100, service: AdminLogsService = Depends(get_admin_logs_service)):
    return await service.get_logs(skip, limit)

@router.patch("/logs/{log_id}/status")
async def update_log_status(log_id: str, status_update: AdminLogStatusUpdate, request: Request, service: AdminLogsService = Depends(get_admin_logs_service)):
    success = await service.update_log_status(log_id, status_update.status)
    if not success:
        raise HTTPException(status_code=404, detail="Log not found")
    return {"message": "Status updated"}

@router.delete("/logs/{log_id}")
async def delete_log(log_id: str, request: Request, service: AdminLogsService = Depends(get_admin_logs_service)):
    success = await service.delete_log(log_id)
    if not success:
        raise HTTPException(status_code=404, detail="Log not found")
    return {"message": "Log deleted"}

@router.get("/platform-analytics", response_model=AdminPlatformAnalyticsResponse)
async def get_platform_analytics(request: Request, service: AdminPlatformAnalyticsService = Depends(get_admin_platform_analytics_service)):
    return await service.get_platform_analytics()

@router.get("/usage-analytics", response_model=AdminUsageAnalyticsResponse)
async def get_usage_analytics(request: Request, service: AdminUsageAnalyticsService = Depends(get_admin_usage_analytics_service)):
    return await service.get_usage_analytics()

@router.get("/cost-analytics", response_model=AdminCostAnalyticsResponse)
async def get_cost_analytics(request: Request, service: AdminCostAnalyticsService = Depends(get_admin_cost_analytics_service)):
    return await service.get_cost_analytics()

@router.get("/multilingual-analytics", response_model=AdminMultilingualAnalyticsResponse)
async def get_multilingual_analytics(request: Request, service: AdminMultilingualAnalyticsService = Depends(get_admin_multilingual_analytics_service)):
    return await service.get_multilingual_analytics()

from app.application.services.admin_security_monitoring_service import AdminSecurityMonitoringService
from app.infrastructure.repositories.security_event_repository import SecurityEventRepository
from app.infrastructure.repositories.pg_audit_log_repository import PgAuditLogRepository
from app.presentation.schemas.admin_schema import AdminSecurityMonitoringResponse

def get_admin_security_monitoring_service(db: AsyncSession = Depends(get_db)) -> AdminSecurityMonitoringService:
    return AdminSecurityMonitoringService(SecurityEventRepository(db), PgAuditLogRepository(db))

@router.get("/security-monitoring", response_model=AdminSecurityMonitoringResponse)
async def get_security_monitoring(request: Request, service: AdminSecurityMonitoringService = Depends(get_admin_security_monitoring_service)):
    return await service.get_security_monitoring()

from app.application.services.admin_error_monitoring_service import AdminErrorMonitoringService
from app.infrastructure.repositories.pg_system_error_repository import PgSystemErrorRepository
from app.presentation.schemas.admin_schema import AdminErrorMonitoringResponse

def get_admin_error_monitoring_service(db: AsyncSession = Depends(get_db)) -> AdminErrorMonitoringService:
    return AdminErrorMonitoringService(PgSystemErrorRepository(db))

@router.get("/error-monitoring", response_model=AdminErrorMonitoringResponse)
async def get_error_monitoring(request: Request, skip: int = 0, limit: int = 100, service: AdminErrorMonitoringService = Depends(get_admin_error_monitoring_service)):
    return await service.get_errors(skip, limit)

from app.application.services.admin_retrieval_evaluation_service import AdminRetrievalEvaluationService
from app.infrastructure.repositories.retrieval_evaluation_repository import RetrievalEvaluationRepository
from app.presentation.schemas.admin_schema import AdminRetrievalEvaluationResponse

def get_admin_retrieval_evaluation_service(db: AsyncSession = Depends(get_db)) -> AdminRetrievalEvaluationService:
    return AdminRetrievalEvaluationService(RetrievalEvaluationRepository(db))

@router.get("/analytics/retrieval-evaluation", response_model=AdminRetrievalEvaluationResponse)
async def get_retrieval_evaluation(request: Request, service: AdminRetrievalEvaluationService = Depends(get_admin_retrieval_evaluation_service)):
    return await service.get_retrieval_evaluation()


from app.application.services.admin_ai_evaluation_service import AdminAIEvaluationService
from app.infrastructure.repositories.ai_evaluation_repository import AIEvaluationRepository
from app.presentation.schemas.admin_schema import AdminAIEvaluationResponse

def get_admin_ai_evaluation_service(db: AsyncSession = Depends(get_db)) -> AdminAIEvaluationService:
    return AdminAIEvaluationService(AIEvaluationRepository(db))

@router.get("/analytics/ai-evaluation", response_model=AdminAIEvaluationResponse)
async def get_ai_evaluation(request: Request, service: AdminAIEvaluationService = Depends(get_admin_ai_evaluation_service)):
    return await service.get_ai_evaluation_metrics()

from app.application.services.admin_research_service import AdminResearchService
from app.infrastructure.repositories.research_repository import ResearchRepository
from app.presentation.schemas.admin_schema import AdminResearchMetricsResponse

def get_admin_research_service(db: AsyncSession = Depends(get_db)) -> AdminResearchService:
    return AdminResearchService(ResearchRepository(db))

@router.get("/analytics/research-metrics", response_model=AdminResearchMetricsResponse)
async def get_research_metrics(request: Request, service: AdminResearchService = Depends(get_admin_research_service)):
    return await service.get_research_metrics()



@router.post("/research/datasets/upload")
async def upload_research_dataset(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    service = AdminResearchService(ResearchRepository(db))
    dataset_id = await service.upload_and_save_dataset(file)
    return {"status": "success", "dataset_id": dataset_id}

@router.post("/research/datasets/{dataset_id}/evaluate")
async def evaluate_research_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db)
):
    service = AdminResearchService(ResearchRepository(db))
    await service.trigger_evaluation(dataset_id)
    return {"status": "success", "message": "Evaluation started in background"}

@router.delete("/research/datasets/{dataset_id}")
async def delete_research_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db)
):
    service = AdminResearchService(ResearchRepository(db))
    success = await service.delete_dataset(dataset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Dataset not found")
    # Need to commit because the repository executed deletes
    await db.commit()
    return {"status": "success", "message": "Dataset deleted"}

from app.application.services.admin_system_settings_service import AdminSystemSettingsService
from app.infrastructure.repositories.system_settings_repository import SystemSettingsRepository
from app.presentation.schemas.admin_schema import (
    LanguageSettingsResponse, LanguageSettingsUpdate, 
    AISettingsResponse, AISettingsUpdate,
    RetrievalSettingsResponse, RetrievalSettingsUpdate,
    IntegrationSettingsResponse, IntegrationSettingsUpdate
)

def get_admin_system_settings_service(db: AsyncSession = Depends(get_db)) -> AdminSystemSettingsService:
    return AdminSystemSettingsService(SystemSettingsRepository(db), audit_log_repo=PgAuditLogRepository(db))

@router.get("/settings/language", response_model=LanguageSettingsResponse)
async def get_language_settings(request: Request, service: AdminSystemSettingsService = Depends(get_admin_system_settings_service)):
    return await service.get_language_settings()

@router.patch("/settings/language", response_model=LanguageSettingsResponse)
async def update_language_settings(update_data: LanguageSettingsUpdate, request: Request, service: AdminSystemSettingsService = Depends(get_admin_system_settings_service)):
    current_user_id = getattr(request.state, "user", {}).get("sub")
    return await service.update_language_settings(
        enabled_languages=update_data.enabled_languages,
        default_language=update_data.default_language,
        translation_pipeline_enabled=update_data.translation_pipeline_enabled,
        current_user_id=current_user_id
    )

@router.get("/settings/ai", response_model=AISettingsResponse)
async def get_ai_settings(request: Request, service: AdminSystemSettingsService = Depends(get_admin_system_settings_service)):
    return await service.get_ai_settings()

@router.patch("/settings/ai", response_model=AISettingsResponse)
async def update_ai_settings(update_data: AISettingsUpdate, request: Request, service: AdminSystemSettingsService = Depends(get_admin_system_settings_service)):
    current_user_id = getattr(request.state, "user", {}).get("sub")
    return await service.update_ai_settings(
        ai_model_name=update_data.ai_model_name,
        ai_temperature=update_data.ai_temperature,
        ai_max_tokens=update_data.ai_max_tokens,
        ai_top_p=update_data.ai_top_p,
        ai_frequency_penalty=update_data.ai_frequency_penalty,
        current_user_id=current_user_id
    )

@router.get("/settings/retrieval", response_model=RetrievalSettingsResponse)
async def get_retrieval_settings(request: Request, service: AdminSystemSettingsService = Depends(get_admin_system_settings_service)):
    return await service.get_retrieval_settings()

@router.patch("/settings/retrieval", response_model=RetrievalSettingsResponse)
async def update_retrieval_settings(update_data: RetrievalSettingsUpdate, request: Request, service: AdminSystemSettingsService = Depends(get_admin_system_settings_service)):
    current_user_id = getattr(request.state, "user", {}).get("sub")
    return await service.update_retrieval_settings(
        retrieval_top_k=update_data.retrieval_top_k,
        retrieval_similarity_threshold=update_data.retrieval_similarity_threshold,
        retrieval_embedding_model=update_data.retrieval_embedding_model,
        retrieval_chunk_size=update_data.retrieval_chunk_size,
        retrieval_chunk_overlap=update_data.retrieval_chunk_overlap,
        current_user_id=current_user_id
    )

@router.get("/settings/integration", response_model=IntegrationSettingsResponse)
async def get_integration_settings(request: Request, service: AdminSystemSettingsService = Depends(get_admin_system_settings_service)):
    return await service.get_integration_settings()

@router.patch("/settings/integration", response_model=IntegrationSettingsResponse)
async def update_integration_settings(update_data: IntegrationSettingsUpdate, request: Request, service: AdminSystemSettingsService = Depends(get_admin_system_settings_service)):
    current_user_id = getattr(request.state, "user", {}).get("sub")
    return await service.update_integration_settings(
        openai_api_key=update_data.openai_api_key,
        twilio_account_sid=update_data.twilio_account_sid,
        twilio_auth_token=update_data.twilio_auth_token,
        whatsapp_phone_number=update_data.whatsapp_phone_number,
        web_socket_url=update_data.web_socket_url,
        current_user_id=current_user_id
    )

@router.get("/settings/security", response_model=SecuritySettingsResponse)
async def get_security_settings(request: Request, service: AdminSystemSettingsService = Depends(get_admin_system_settings_service)):
    return await service.get_security_settings()

@router.patch("/settings/security", response_model=SecuritySettingsResponse)
async def update_security_settings(update_data: SecuritySettingsUpdate, request: Request, service: AdminSystemSettingsService = Depends(get_admin_system_settings_service)):
    current_user_id = getattr(request.state, "user", {}).get("sub")
    return await service.update_security_settings(
        jwt_expiry_minutes=update_data.jwt_expiry_minutes,
        rate_limit_per_minute=update_data.rate_limit_per_minute,
        prompt_validation_enabled=update_data.prompt_validation_enabled,
        account_lockout_threshold=update_data.account_lockout_threshold,
        current_user_id=current_user_id
    )
