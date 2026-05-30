from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.base import get_db
from app.application.services.admin_service import AdminService
from app.presentation.schemas.admin_schema import AdminOverviewResponse

from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.repositories.chat_repository import ChatRepository
from app.infrastructure.repositories.document_repository import DocumentRepository
from app.infrastructure.repositories.pg_llm_log_repository import PgLLMLogRepository

router = APIRouter(prefix="/admin", tags=["Admin"])

def get_admin_service(db: AsyncSession = Depends(get_db)) -> AdminService:
    user_repo = UserRepository(db)
    chat_repo = ChatRepository(db)
    document_repo = DocumentRepository(db)
    llm_log_repo = PgLLMLogRepository(db)
    return AdminService(user_repo, chat_repo, document_repo, llm_log_repo)

@router.get("/overview", response_model=AdminOverviewResponse)
async def get_overview(
    request: Request,
    service: AdminService = Depends(get_admin_service)
):
    """Get dynamic overview statistics for the admin dashboard."""
    # Currently just requiring basic Auth middleware which injects request.state.user.
    # To restrict strictly to Admins, role checks can be added here.
    return await service.get_overview_stats()

from app.presentation.schemas.admin_schema import AdminUserListResponse, AdminUserStatusUpdate, AdminUserItem
from fastapi import HTTPException

@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    service: AdminService = Depends(get_admin_service)
):
    """List all users for the admin dashboard."""
    return await service.get_users(skip, limit)

@router.patch("/users/{user_id}/status", response_model=AdminUserItem)
async def update_user_status(
    user_id: str,
    status_update: AdminUserStatusUpdate,
    request: Request,
    service: AdminService = Depends(get_admin_service)
):
    """Block or unblock a user."""
    try:
        return await service.update_user_status(user_id, status_update.is_active)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

from app.presentation.schemas.admin_schema import AdminKnowledgeResponse, AdminRetrievalMonitoringResponse

@router.get("/retrieval-monitoring", response_model=AdminRetrievalMonitoringResponse)
async def get_retrieval_monitoring(
    request: Request,
    service: AdminService = Depends(get_admin_service)
):
    """Get retrieval monitoring metrics for the admin dashboard."""
    return await service.get_retrieval_monitoring()

@router.get("/knowledge", response_model=AdminKnowledgeResponse)
async def get_knowledge(
    request: Request,
    service: AdminService = Depends(get_admin_service)
):
    """Get knowledge monitoring metrics for the admin dashboard."""
    return await service.get_knowledge_metrics()

from app.presentation.schemas.admin_schema import AdminLogListResponse, AdminLogStatusUpdate

@router.get("/logs", response_model=AdminLogListResponse)
async def get_logs(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    service: AdminService = Depends(get_admin_service)
):
    """Get all logs for the admin dashboard."""
    return await service.get_logs(skip, limit)

@router.patch("/logs/{log_id}/status")
async def update_log_status(
    log_id: str,
    status_update: AdminLogStatusUpdate,
    request: Request,
    service: AdminService = Depends(get_admin_service)
):
    """Update log status."""
    success = await service.update_log_status(log_id, status_update.status)
    if not success:
        raise HTTPException(status_code=404, detail="Log not found")
    return {"message": "Status updated"}

@router.delete("/logs/{log_id}")
async def delete_log(
    log_id: str,
    request: Request,
    service: AdminService = Depends(get_admin_service)
):
    """Delete a log."""
    success = await service.delete_log(log_id)
    if not success:
        raise HTTPException(status_code=404, detail="Log not found")
    return {"message": "Log deleted"}
