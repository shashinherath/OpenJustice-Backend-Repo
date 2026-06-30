from typing import List

from app.infrastructure.repositories.security_event_repository import SecurityEventRepository
from app.infrastructure.repositories.pg_audit_log_repository import PgAuditLogRepository
from app.presentation.schemas.admin_schema import (
    AdminSecurityMonitoringResponse,
    SecuritySignal,
    MonitoringArea,
    PriorityAlert,
    SecurityEventRecord,
    ActivityLogItem
)


class AdminSecurityMonitoringService:
    def __init__(
        self,
        security_event_repository: SecurityEventRepository,
        audit_log_repository: PgAuditLogRepository
    ):
        self.security_event_repository = security_event_repository
        self.audit_log_repository = audit_log_repository

    async def get_security_monitoring(self) -> AdminSecurityMonitoringResponse:
        # 1. Fetch recent events
        recent_events_raw = await self.security_event_repository.get_recent_events(limit=5)
        recent_events = [
            SecurityEventRecord(
                area=e.area,
                source=e.source,
                detail=e.detail,
                severity=e.severity,
                timestamp=e.created_at.strftime("%Y-%m-%d %H:%M")
            )
            for e in recent_events_raw
        ]

        # 2. Fetch priority alerts
        priority_alerts_raw = await self.security_event_repository.get_priority_alerts(limit=3)
        priority_alerts = [
            PriorityAlert(
                title=f"{e.area} Alert",
                detail=e.detail,
                severity=e.severity
            )
            for e in priority_alerts_raw
        ]

        # 3. Compute counts for Signals & Monitoring Areas
        prompt_injection_count = await self.security_event_repository.get_count_by_area("Prompt Injection", 24)
        failed_logins_count = await self.security_event_repository.get_count_by_area("Failed Logins", 24)
        rate_limits_count = await self.security_event_repository.get_count_by_area("Rate Limits", 24)
        jwt_activity_count = await self.security_event_repository.get_count_by_area("JWT Activity", 24)

        # Build Signals
        signals = [
            SecuritySignal(
                label="Prompt Injection Attempts",
                value=str(prompt_injection_count),
                note="Detected in last 24h",
                tone="rose" if prompt_injection_count > 100 else "amber" if prompt_injection_count > 0 else "emerald"
            ),
            SecuritySignal(
                label="Failed Logins",
                value=str(failed_logins_count),
                note="Across web and mobile",
                tone="amber" if failed_logins_count > 20 else "emerald"
            ),
            SecuritySignal(
                label="Rate Limit Events",
                value=str(rate_limits_count),
                note="Throttled safely",
                tone="emerald"
            ),
            SecuritySignal(
                label="JWT Activity",
                value=f"{jwt_activity_count} anomalies",
                note="Invalid/expired/replay",
                tone="violet"
            )
        ]

        # Build Monitoring Areas
        monitoring_areas = [
            MonitoringArea(
                key="prompt-injection",
                title="Prompt Injection",
                icon="psychology",
                status="Needs Action" if prompt_injection_count > 50 else ("Watch" if prompt_injection_count > 10 else "Healthy"),
                summary="Adversarial prompts are being blocked, monitor severity.",
                metricLabel="Blocks (24h)",
                metricValue=str(prompt_injection_count)
            ),
            MonitoringArea(
                key="failed-logins",
                title="Failed Logins",
                icon="vpn_key",
                status="Watch" if failed_logins_count > 5 else "Healthy",
                summary="Lockout policy is containing failed login bursts.",
                metricLabel="Lockouts (24h)",
                metricValue=str(failed_logins_count)
            ),
            MonitoringArea(
                key="rate-limits",
                title="Rate Limits",
                icon="speed",
                status="Healthy",
                summary="Throttling is active and protecting upstream services.",
                metricLabel="Throttled requests",
                metricValue=str(rate_limits_count)
            ),
            MonitoringArea(
                key="jwt-activity",
                title="JWT Activity",
                icon="token",
                status="Watch" if jwt_activity_count > 0 else "Healthy",
                summary="Token validation catches expiry and replay attempts.",
                metricLabel="Invalid tokens",
                metricValue=str(jwt_activity_count)
            )
        ]

        # 4. Fetch recent activity logs
        activities_raw = await self.audit_log_repository.get_recent_activities(limit=10)
        activity_logs = [
            ActivityLogItem(
                id=str(a.id),
                user_email=a.user.email if a.user else "System",
                action=a.action or "Unknown Action",
                entity=a.entity or "N/A",
                timestamp=a.created_at.strftime("%Y-%m-%d %H:%M")
            )
            for a in activities_raw
        ]

        return AdminSecurityMonitoringResponse(
            signals=signals,
            monitoring_areas=monitoring_areas,
            priority_alerts=priority_alerts,
            recent_events=recent_events,
            activity_logs=activity_logs
        )
