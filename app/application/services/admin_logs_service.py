from app.domain.interfaces.llm_log_repository import ILLMLogRepository
from app.domain.interfaces.audio_log_repository import IAudioLogRepository
from app.domain.interfaces.retrieval_log_repository import IRetrievalLogRepository

class AdminLogsService:
    def __init__(
        self, 
        llm_log_repo: ILLMLogRepository, 
        audio_log_repo: IAudioLogRepository, 
        retrieval_log_repo: IRetrievalLogRepository
    ):
        self.llm_log_repo = llm_log_repo
        self.audio_log_repo = audio_log_repo
        self.retrieval_log_repo = retrieval_log_repo

    async def get_logs(self, skip: int = 0, limit: int = 100) -> dict:
        fetch_limit = skip + limit
        total_llm, llm_logs = await self.llm_log_repo.get_logs(0, fetch_limit)
        total_audio, audio_logs = await self.audio_log_repo.get_logs(0, fetch_limit)
        total_retrieval, retrieval_logs = await self.retrieval_log_repo.get_logs(0, fetch_limit)
        
        total = total_llm + total_audio + total_retrieval
        trace_logs = []
        
        status_map = {
            "success": "Completed",
            "error": "Failed",
            "pending": "Pending",
            "Reviewed": "Reviewed",
            "Completed": "Completed",
            "Failed": "Failed",
            "Pending": "Pending"
        }
        
        for log in llm_logs:
            mapped_status = status_map.get(log.status, log.status or "Pending")
            
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
                "timestamp": log.created_at.strftime("%Y-%m-%d %H:%M") if log.created_at else "",
                "_created_at": log.created_at
            })
            
        for log in audio_logs:
            event_type = f"{log.audio_type}_request" if log.audio_type else "stt_request"
            
            trace_logs.append({
                "id": str(log.id),
                "correlationId": str(log.id),
                "eventType": event_type,
                "model": log.provider or "unknown",
                "promptVersion": "N/A",
                "language": log.language or "auto",
                "promptTokens": 0,
                "completionTokens": 0,
                "latencyMs": int((log.duration_seconds or 0) * 1000),
                "retrievalCount": 0,
                "citationCount": 0,
                "status": "Completed",
                "timestamp": log.created_at.strftime("%Y-%m-%d %H:%M") if log.created_at else "",
                "_created_at": log.created_at
            })
            
        for log in retrieval_logs:
            trace_logs.append({
                "id": str(log.id),
                "correlationId": str(log.conversation_id) if log.conversation_id else str(log.id),
                "eventType": "retrieval_results",
                "model": "retrieval-engine",
                "promptVersion": "N/A",
                "language": log.language or "English",
                "promptTokens": 0,
                "completionTokens": 0,
                "latencyMs": log.retrieval_latency_ms or 0,
                "retrievalCount": len(log.retrieved_documents) if log.retrieved_documents else 0,
                "citationCount": 0,
                "status": "Completed",
                "timestamp": log.created_at.strftime("%Y-%m-%d %H:%M") if log.created_at else "",
                "_created_at": log.created_at
            })
            
        # Sort combined logs by _created_at desc
        trace_logs.sort(key=lambda x: x["_created_at"], reverse=True)
        
        # Paginate
        paginated_logs = trace_logs[skip : skip + limit]
        
        # Remove internal sorting key
        for log in paginated_logs:
            del log["_created_at"]
            
        # Get global stats
        llm_stats = await self.llm_log_repo.get_stats()
        audio_stats = await self.audio_log_repo.get_stats()
        retrieval_stats = await self.retrieval_log_repo.get_stats()
        
        total_completed = llm_stats["completed"] + audio_stats["completed"] + retrieval_stats["completed"]
        
        total_lat = llm_stats["total_latency"] + audio_stats["total_latency"] + retrieval_stats["total_latency"]
        lat_count = llm_stats["latency_count"] + audio_stats["latency_count"] + retrieval_stats["latency_count"]
        global_avg_latency = total_lat / lat_count if lat_count > 0 else 0
            
        return {
            "logs": paginated_logs,
            "total": total,
            "total_completed": int(total_completed),
            "total_reviewed": int(llm_stats["reviewed"]),
            "total_pending": int(llm_stats["pending"]),
            "total_failed": int(llm_stats["failed"]),
            "total_tokens": int(llm_stats["total_tokens"]),
            "avg_latency": int(global_avg_latency)
        }

    async def update_log_status(self, log_id: str, status: str) -> bool:
        from uuid import UUID
        return await self.llm_log_repo.update_log_status(UUID(log_id), status)

    async def delete_log(self, log_id: str) -> bool:
        from uuid import UUID
        return await self.llm_log_repo.delete_log(UUID(log_id))
