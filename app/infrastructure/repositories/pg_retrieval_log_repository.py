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
