from app.domain.interfaces.llm_log_repository import ILLMLogRepository

class AdminLogsService:
    def __init__(self, llm_log_repo: ILLMLogRepository):
        self.llm_log_repo = llm_log_repo

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
