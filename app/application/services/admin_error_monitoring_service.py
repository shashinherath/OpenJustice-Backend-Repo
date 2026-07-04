from typing import Dict, Any
from app.domain.interfaces.system_error_repository import ISystemErrorRepository

class AdminErrorMonitoringService:
    def __init__(self, system_error_repo: ISystemErrorRepository):
        self.system_error_repo = system_error_repo

    async def get_errors(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        total, errors = await self.system_error_repo.get_errors(skip, limit)
        stats = await self.system_error_repo.get_stats()
        
        error_records = []
        for err in errors:
            error_records.append({
                "id": str(err.id),
                "type": err.error_type,
                "message": err.message,
                "timestamp": err.created_at.strftime("%Y-%m-%d %H:%M") if err.created_at else "",
                "details": err.details
            })
            
        return {
            "errors": error_records,
            "total_errors": stats.get("total", 0),
            "total_llm": stats.get("llm", 0),
            "total_db": stats.get("db", 0),
            "total_api": stats.get("api", 0),
            "total_auth": stats.get("auth", 0),
            "total_system": stats.get("system", 0)
        }
