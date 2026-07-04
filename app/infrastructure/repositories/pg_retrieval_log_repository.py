from typing import List
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.interfaces.retrieval_log_repository import IRetrievalLogRepository
from app.infrastructure.models.retrieval_log import RetrievalLog
from app.infrastructure.models.retrieved_document import RetrievedDocument

class PgRetrievalLogRepository(IRetrievalLogRepository):
    """PostgreSQL implementation of RAG Telemetry."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_retrieval(
        self, 
        conversation_id: uuid.UUID | None, 
        query: str, 
        language: str, 
        top_k: int, 
        retrieved_chunks: List[dict],
        latency_ms: int = None
    ) -> uuid.UUID:
        # Create log entry
        log_entry = RetrievalLog(
            conversation_id=conversation_id, # Integer expected in model? Wait, it's defined as Integer in model! Let me check retrieval_log.py
            query=query,
            language=language,
            top_k=top_k,
            retrieval_latency_ms=latency_ms
        )
        self.session.add(log_entry)
        await self.session.flush() # get ID
        
        # Create linked documents
        for chunk in retrieved_chunks:
            doc = RetrievedDocument(
                retrieval_log_id=log_entry.id,
                document_chunk_id=chunk["chunk_id"],
                similarity_score=chunk.get("similarity_score", 0.0)
            )
            self.session.add(doc)
            
        await self.session.commit()
        return log_entry.id

    async def get_logs(self, skip: int = 0, limit: int = 100) -> tuple[int, list]:
        from sqlalchemy import select, func
        from sqlalchemy.orm import joinedload
        total_result = await self.session.execute(select(func.count(RetrievalLog.id)))
        total = total_result.scalar_one_or_none() or 0
        
        result = await self.session.execute(
            select(RetrievalLog).options(joinedload(RetrievalLog.retrieved_documents)).order_by(RetrievalLog.created_at.desc()).offset(skip).limit(limit)
        )
        logs = list(result.unique().scalars().all())
        return total, logs

    async def get_stats(self) -> dict:
        from sqlalchemy import select, func
        
        result = await self.session.execute(
            select(
                func.count(RetrievalLog.id),
                func.avg(RetrievalLog.retrieval_latency_ms)
            )
        )
        
        count, avg_latency = result.first() or (0, 0)
        return {
            "completed": int(count or 0),
            "avg_latency": float(avg_latency or 0),
            "total_latency": float(avg_latency or 0) * int(count or 0),
            "latency_count": int(count or 0)
        }
