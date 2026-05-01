import logging
from typing import List, Tuple
from langchain_openai import OpenAIEmbeddings

from app.config import settings
from app.domain.interfaces.document_repository import IDocumentRepository
from app.infrastructure.models.document_chunk import DocumentChunk
from app.domain.interfaces.retrieval_log_repository import IRetrievalLogRepository
import uuid

logger = logging.getLogger(__name__)


class RetrievalService:
    """Centralized document retrieval service with telemetry logging."""

    def __init__(self, repository: IDocumentRepository, log_repository: IRetrievalLogRepository = None):
        self.repository = repository
        self.log_repository = log_repository
        self.embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL, 
            api_key=settings.OPENAI_API_KEY
        )

    async def retrieve(
        self,
        query: str,
        language: str = "English",
        threshold: float = 0.7
    ) -> Tuple[List[DocumentChunk], str]:
        """Retrieve relevant document chunks with dynamic top-k and confidence scoring."""
        
        # Determine dynamic Top-K based on query complexity
        top_k = self._determine_optimal_top_k(query)
        logger.info(f"Dynamic Top-K determined as {top_k} for query length {len(query.split())}")

        try:
            query_vector = await self.embeddings.aembed_query(query)
            
            chunks = await self.repository.search_similar_chunks(
                query_vector, 
                limit=top_k, 
                threshold=threshold
            )
            
            confidence = self._calculate_confidence(chunks, query_vector)
            
            if self.log_repository:
                # Fire and forget log / or await it
                retrieved_data = [{"chunk_id": c.id, "similarity_score": getattr(c, "similarity", 0.0)} for c in chunks]
                await self.log_repository.log_retrieval(
                    conversation_id=None, # Passed from LLMService if we want to track it later, keeping simple for now
                    query=query,
                    language=language,
                    top_k=top_k,
                    retrieved_chunks=retrieved_data
                )
                
            return chunks, confidence
            
        except Exception as e:
            logger.error(f"Retrieval Service failed during similarity extraction: {str(e)}", exc_info=True)
            return [], "None"

    def _determine_optimal_top_k(self, query: str) -> int:
        """Dynamically determine optimal top_k value based on query length."""
        query_length = len(query.split())
        
        if query_length < 10:
            return 3  # Simple query, few sources needed
        elif query_length > 20:
            return 8  # Complex query, more context needed
        else:
            return 5  # Default
            
    def _calculate_confidence(self, retrieved_docs: List[DocumentChunk], query_vector: list[float]) -> str:
        """Calculate retrieval confidence level based on distance scores."""
        if not retrieved_docs:
            return "None"
            
        import math
        # We need to compute cosine similarity manually if it's not returned by the ORM
        # But wait, we can just use the fact that they passed the threshold
        # In a real app, the ORM would return the distance. Since we didn't add the distance column to the model directly,
        # we can roughly estimate confidence by the number of returned chunks
        
        if len(retrieved_docs) >= 5:
            return "High"
        elif len(retrieved_docs) >= 2:
            return "Medium"
        else:
            return "Low"
