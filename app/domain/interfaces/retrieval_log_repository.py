from abc import ABC, abstractmethod
from typing import List
import uuid

class IRetrievalLogRepository(ABC):
    """Interface for logging vector search retrieval traceability."""
    
    @abstractmethod
    async def log_retrieval(
        self, 
        conversation_id: uuid.UUID | None, 
        query: str, 
        language: str, 
        top_k: int, 
        retrieved_chunks: List[dict]
    ) -> uuid.UUID:
        """
        Logs the retrieval action and the exact chunks returned.
        retrieved_chunks is a list of dicts: {"chunk_id": uuid, "similarity_score": float}
        Returns the retrieval_log_id.
        """
        pass
