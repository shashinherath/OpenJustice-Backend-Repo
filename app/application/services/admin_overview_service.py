from app.domain.interfaces.user_repository import IUserRepository
from app.domain.interfaces.chat_repository import IChatRepository
from app.domain.interfaces.document_repository import IDocumentRepository
from app.domain.interfaces.llm_log_repository import ILLMLogRepository
from app.domain.interfaces.audit_log_repository import IAuditLogRepository

from app.presentation.schemas.admin_schema import (
    AdminOverviewResponse,
    StatItem,
    ActivityItem,
    ServiceStatusItem,
    DataSourceItem,
    DailyQueryStat,
    QuickActionItem
)

class AdminOverviewService:
    def __init__(
        self, 
        user_repo: IUserRepository,
        chat_repo: IChatRepository,
        document_repo: IDocumentRepository,
        llm_log_repo: ILLMLogRepository,
        audit_log_repo: IAuditLogRepository
    ):
        self.user_repo = user_repo
        self.chat_repo = chat_repo
        self.document_repo = document_repo
        self.llm_log_repo = llm_log_repo
        self.audit_log_repo = audit_log_repo

    async def get_overview_stats(self) -> AdminOverviewResponse:
        # 1. Total Users
        total_users = await self.user_repo.get_total_count()
        active_sessions = await self.user_repo.get_active_sessions_count()

        # 2. Total Queries
        total_queries = await self.chat_repo.get_user_message_count()
        whatsapp_requests = await self.chat_repo.get_whatsapp_requests_count()
        voice_queries = await self.chat_repo.get_voice_queries_count()

        # 3. Total Documents
        total_documents = await self.document_repo.get_total_count()
        total_chunks = await self.document_repo.get_total_chunks_count()

        # 4. Total Errors
        total_errors = await self.llm_log_repo.get_error_count()
        ai_responses_today = await self.llm_log_repo.get_responses_today_count()
        avg_response_time = await self.llm_log_repo.get_avg_response_time()

        stats = [
            StatItem(id=1, title="Total Users", value=f"{total_users:,}", change="+12%", statusType="positive"),
            StatItem(id=2, title="Active Sessions", value=f"{active_sessions:,}", change="+5%", statusType="positive"),
            StatItem(id=3, title="Total Queries", value=f"{total_queries:,}", change="+18%", statusType="positive"),
            StatItem(id=4, title="Documents Indexed", value=f"{total_documents:,}", change="+3%", statusType="positive"),
            StatItem(id=5, title="Total Chunks", value=f"{total_chunks:,}", change="+8%", statusType="positive"),
            StatItem(id=6, title="AI Responses Today", value=f"{ai_responses_today:,}", change="+22%", statusType="positive"),
            StatItem(id=7, title="Errors Today", value=f"{total_errors:,}", change="-2%", statusType="neutral"),
            StatItem(id=8, title="WhatsApp Requests", value=f"{whatsapp_requests:,}", change="+9%", statusType="positive"),
            StatItem(id=9, title="Voice Queries", value=f"{voice_queries:,}", change="+4%", statusType="positive"),
            StatItem(id=10, title="Avg Response Time", value=f"{int(avg_response_time)}ms", change="-15%", statusType="positive"),
            StatItem(id=11, title="Retrieval Accuracy", value="94.2%", change="+1.3%", statusType="positive"),
            StatItem(id=12, title="System Health", value="98.6%", change="+0.5%", statusType="positive"),
        ]

        recent_logs = await self.audit_log_repo.get_recent_activities(limit=5)
        activities = []
        for idx, log in enumerate(recent_logs):
            user_email = log.user.email if log.user else None
            activities.append(ActivityItem(
                id=idx + 1,
                title=log.action or "System Event",
                description=f"Entity: {log.entity} ({log.entity_id})" if log.entity else "General activity",
                timeAgo=log.created_at.strftime("%Y-%m-%d %H:%M"),
                icon="history",
                iconColorClass="text-cyan-300",
                userEmail=user_email
            ))
        if not activities:
            activities = [
                ActivityItem(
                    id=1,
                    title="System Operational",
                    description="Live metrics currently being tracked.",
                    timeAgo="Just now",
                    icon="check_circle",
                    iconColorClass="text-green-500"
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
        qpd_data = await self.chat_repo.get_queries_per_day(7)
        
        from datetime import datetime, timedelta, timezone
        days_dict = {}
        for i in range(6, -1, -1):
            d = datetime.now(timezone.utc) - timedelta(days=i)
            day_str = d.strftime("%a")
            days_dict[day_str] = 0
            
        for d in qpd_data:
            if d['date'] in days_dict:
                days_dict[d['date']] = d['count']
                
        max_q = max(list(days_dict.values()) + [1])
        queries_per_day = []
        for d_str, count in days_dict.items():
            pct = int((count / max_q) * 100)
            queries_per_day.append(DailyQueryStat(
                date=d_str,
                count=count,
                heightPercentage=f"{pct}%"
            ))

        quick_actions = [
            QuickActionItem(icon="refresh", label="Clear Semantic Cache", highlight=False, action_id="clear_semantic_cache"),
            QuickActionItem(icon="download", label="Export Report", highlight=False, action_id="export_report"),
        ]

        return AdminOverviewResponse(
            stats=stats,
            activities=activities,
            core_services=core_services,
            data_sources=data_sources,
            queries_per_day=queries_per_day,
            quick_actions=quick_actions
        )
