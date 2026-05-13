from app.domain.interfaces.user_repository import IUserRepository
from app.domain.interfaces.chat_repository import IChatRepository
from app.domain.interfaces.document_repository import IDocumentRepository
from app.domain.interfaces.llm_log_repository import ILLMLogRepository

from app.presentation.schemas.admin_schema import (
    AdminOverviewResponse,
    StatItem,
    ActivityItem,
    ServiceStatusItem,
    DataSourceItem
)

class AdminService:
    def __init__(
        self, 
        user_repo: IUserRepository,
        chat_repo: IChatRepository,
        document_repo: IDocumentRepository,
        llm_log_repo: ILLMLogRepository
    ):
        self.user_repo = user_repo
        self.chat_repo = chat_repo
        self.document_repo = document_repo
        self.llm_log_repo = llm_log_repo

    async def get_overview_stats(self) -> AdminOverviewResponse:
        # 1. Total Users
        total_users = await self.user_repo.get_total_count()

        # 2. Total Queries (Messages where sender == 'user')
        total_queries = await self.chat_repo.get_user_message_count()

        # 3. Total Documents
        total_documents = await self.document_repo.get_total_count()

        # 4. Total Errors (LLMRequests where status == 'error')
        total_errors = await self.llm_log_repo.get_error_count()

        stats = [
            StatItem(
                id=1,
                title="Total Users",
                value=f"{total_users:,}",
                change="Live",
                statusType="neutral"
            ),
            StatItem(
                id=2,
                title="Total Queries",
                value=f"{total_queries:,}",
                change="Live",
                statusType="neutral"
            ),
            StatItem(
                id=3,
                title="Total Documents",
                value=f"{total_documents:,}",
                change="Live",
                statusType="positive" if total_documents > 0 else "neutral"
            ),
            StatItem(
                id=4,
                title="Total Errors",
                value=f"{total_errors:,}",
                change="Needs review" if total_errors > 0 else "All clear",
                statusType="warning" if total_errors > 0 else "positive"
            )
        ]

        # Mocked Activities (Can be wired up to actual Audit Logs later)
        activities = [
            ActivityItem(
                id=1,
                title="System Operational",
                description="Live metrics currently being tracked.",
                timeAgo="Just now",
                icon="check_circle",
                iconColorClass="text-green-500"
            ),
            ActivityItem(
                id=2,
                title="Database Sync: Federal Statutes",
                description="Background worker actively syncing.",
                timeAgo="14 mins ago",
                icon="sync",
                iconColorClass="text-cyan-300"
            )
        ]

        # Core Services
        core_services = [
            ServiceStatusItem(id=1, title="LLM Status", status="Active"),
            ServiceStatusItem(id=2, title="Database Status", status="Active"),
            ServiceStatusItem(id=3, title="Vector DB Status", status="Active"),
        ]

        # Data Sources
        data_sources = [
            DataSourceItem(
                id=1,
                title="Federal Statutes",
                statusLabel="Healthy",
                statusColorClass="text-green-500",
                progressPercent=100,
                footerText="Synced"
            ),
            DataSourceItem(
                id=2,
                title="Supreme Court Opinions",
                statusLabel="Healthy",
                statusColorClass="text-green-500",
                progressPercent=100,
                footerText="Synced"
            )
        ]

        return AdminOverviewResponse(
            stats=stats,
            activities=activities,
            core_services=core_services,
            data_sources=data_sources
        )

    async def get_users(self, skip: int = 0, limit: int = 100) -> dict:
        users = await self.user_repo.list_users(skip, limit)
        user_items = []
        total_active = 0
        total_blocked = 0

        for user in users:
            if user.is_active:
                total_active += 1
            else:
                total_blocked += 1

            user_items.append({
                "id": str(user.id),
                "email": user.email or "",
                "status": "Active" if user.is_active else "Blocked",
                "createdDate": user.created_at.strftime("%Y-%m-%d") if user.created_at else ""
            })

        return {
            "users": user_items,
            "total_active": total_active,
            "total_blocked": total_blocked
        }

    async def update_user_status(self, user_id: str, is_active: bool) -> dict:
        from uuid import UUID
        updated_user = await self.user_repo.update_status(UUID(user_id), is_active)
        if not updated_user:
            raise ValueError(f"User with ID {user_id} not found.")
        return {
            "id": str(updated_user.id),
            "email": updated_user.email or "",
            "status": "Active" if updated_user.is_active else "Blocked",
            "createdDate": updated_user.created_at.strftime("%Y-%m-%d") if updated_user.created_at else ""
        }

    async def get_knowledge_metrics(self) -> dict:
        records = await self.document_repo.get_knowledge_metrics()
        return {"records": records}
