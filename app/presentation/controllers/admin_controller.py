from fastapi import APIRouter, Depends, Request, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.base import get_db
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.repositories.chat_repository import ChatRepository
from app.infrastructure.repositories.document_repository import DocumentRepository
from app.infrastructure.repositories.pg_llm_log_repository import PgLLMLogRepository

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
    AdminCostAnalyticsResponse, AdminMultilingualAnalyticsResponse
)

router = APIRouter(prefix="/admin", tags=["Admin"])

def get_admin_overview_service(db: AsyncSession = Depends(get_db)) -> AdminOverviewService:
    return AdminOverviewService(UserRepository(db), ChatRepository(db), DocumentRepository(db), PgLLMLogRepository(db))

def get_admin_users_service(db: AsyncSession = Depends(get_db)) -> AdminUsersService:
    return AdminUsersService(UserRepository(db))

def get_admin_knowledge_service(db: AsyncSession = Depends(get_db)) -> AdminKnowledgeService:
    return AdminKnowledgeService(DocumentRepository(db))

def get_admin_logs_service(db: AsyncSession = Depends(get_db)) -> AdminLogsService:
    return AdminLogsService(PgLLMLogRepository(db))

def get_admin_retrieval_service(db: AsyncSession = Depends(get_db)) -> AdminRetrievalService:
    return AdminRetrievalService(DocumentRepository(db))

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

@router.get("/users", response_model=AdminUserListResponse)
async def list_users(request: Request, skip: int = 0, limit: int = 100, service: AdminUsersService = Depends(get_admin_users_service)):
    return await service.get_users(skip, limit)

@router.patch("/users/{user_id}/status", response_model=AdminUserItem)
async def update_user_status(user_id: str, status_update: AdminUserStatusUpdate, request: Request, service: AdminUsersService = Depends(get_admin_users_service)):
    try:
        return await service.update_user_status(user_id, status_update.is_active)
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
