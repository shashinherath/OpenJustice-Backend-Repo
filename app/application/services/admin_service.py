from app.domain.interfaces.user_repository import IUserRepository
from app.domain.interfaces.chat_repository import IChatRepository
from app.domain.interfaces.document_repository import IDocumentRepository
from app.domain.interfaces.llm_log_repository import ILLMLogRepository

from app.presentation.schemas.admin_schema import (
    AdminOverviewResponse,
    StatItem,
    ActivityItem,
    ServiceStatusItem,
    DataSourceItem,
    DailyQueryStat
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
            StatItem(id=1, title="Total Users", value=f"{total_users:,}", change="+12%", statusType="positive"),
            StatItem(id=2, title="Active Sessions", value="342", change="+5%", statusType="positive"),
            StatItem(id=3, title="Total Queries", value=f"{total_queries:,}", change="+18%", statusType="positive"),
            StatItem(id=4, title="Documents Indexed", value=f"{total_documents:,}", change="+3%", statusType="positive"),
            StatItem(id=5, title="Total Chunks", value="48,942", change="+8%", statusType="positive"),
            StatItem(id=6, title="AI Responses Today", value="3,621", change="+22%", statusType="positive"),
            StatItem(id=7, title="Errors Today", value=f"{total_errors:,}", change="-2%", statusType="neutral"),
            StatItem(id=8, title="WhatsApp Requests", value="487", change="+9%", statusType="positive"),
            StatItem(id=9, title="Voice Queries", value="156", change="+4%", statusType="positive"),
            StatItem(id=10, title="Avg Response Time", value="842ms", change="-15%", statusType="positive"),
            StatItem(id=11, title="Retrieval Accuracy", value="94.2%", change="+1.3%", statusType="positive"),
            StatItem(id=12, title="System Health", value="98.6%", change="+0.5%", statusType="positive"),
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
            ServiceStatusItem(id=1, title="OpenAI API", status="Active", icon="api"),
            ServiceStatusItem(id=2, title="PostgreSQL", status="Active", icon="database"),
            ServiceStatusItem(id=3, title="pgvector", status="Active", icon="storage"),
            ServiceStatusItem(id=4, title="WebSocket Server", status="Active", icon="cloud"),
            ServiceStatusItem(id=5, title="WhatsApp API", status="Active", icon="chat"),
            ServiceStatusItem(id=6, title="Translation Service", status="Active", icon="translate"),
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
        
        # Queries Per Day
        queries_per_day = [
            DailyQueryStat(date="Mon", count=462, heightPercentage="65%"),
            DailyQueryStat(date="Tue", count=512, heightPercentage="83%"),
            DailyQueryStat(date="Wed", count=488, heightPercentage="79%"),
            DailyQueryStat(date="Thu", count=556, heightPercentage="90%"),
            DailyQueryStat(date="Fri", count=603, heightPercentage="100%"),
            DailyQueryStat(date="Sat", count=421, heightPercentage="68%"),
            DailyQueryStat(date="Sun", count=394, heightPercentage="64%"),
        ]

        return AdminOverviewResponse(
            stats=stats,
            activities=activities,
            core_services=core_services,
            data_sources=data_sources,
            queries_per_day=queries_per_day
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

    async def get_logs(self, skip: int = 0, limit: int = 100) -> dict:
        total, logs = await self.llm_log_repo.get_logs(skip, limit)
        trace_logs = []
        for log in logs:
            # Map status
            status_map = {
                "success": "Completed",
                "error": "Failed",
                "pending": "Pending",
                "Reviewed": "Reviewed",
                "Completed": "Completed",
                "Failed": "Failed",
                "Pending": "Pending"
            }
            mapped_status = status_map.get(log.status, log.status or "Pending")
            
            # Map event type
            event_type = "llm_request"
            if mapped_status == "Completed" or mapped_status == "Reviewed":
                event_type = "llm_response"
            elif mapped_status == "Failed":
                event_type = "llm_error"
                
            trace_logs.append({
                "id": str(log.id),
                "correlationId": str(log.correlation_id) if log.correlation_id else str(log.id),
                "eventType": event_type,
                "model": log.model_name or "unknown",
                "promptVersion": log.prompt_version or "N/A",
                "language": "English",
                "promptTokens": log.prompt_tokens or 0,
                "completionTokens": log.completion_tokens or 0,
                "latencyMs": log.latency_ms or 0,
                "retrievalCount": 0,
                "citationCount": 0,
                "status": mapped_status,
                "timestamp": log.created_at.strftime("%Y-%m-%d %H:%M") if log.created_at else ""
            })
            
        return {
            "logs": trace_logs,
            "total": total
        }

    async def update_log_status(self, log_id: str, status: str) -> bool:
        from uuid import UUID
        return await self.llm_log_repo.update_log_status(UUID(log_id), status)

    async def delete_log(self, log_id: str) -> bool:
        from uuid import UUID
        return await self.llm_log_repo.delete_log(UUID(log_id))
