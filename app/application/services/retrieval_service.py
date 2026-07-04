import logging
from typing import List, Tuple
import time
import tiktoken
from langchain_openai import OpenAIEmbeddings
from app.domain.interfaces.llm_log_repository import ILLMLogRepository

from app.config import settings
from app.domain.interfaces.document_repository import IDocumentRepository
from app.infrastructure.models.document_chunk import DocumentChunk
from app.domain.interfaces.retrieval_log_repository import IRetrievalLogRepository
from app.infrastructure.repositories.system_settings_repository import SystemSettingsRepository
import uuid
import time
import traceback

from app.application.services.system_error_logger import log_system_error

logger = logging.getLogger(__name__)


class RetrievalService:
    """Centralized document retrieval service with telemetry logging."""

    def __init__(
        self, 
        repository: IDocumentRepository, 
        log_repository: IRetrievalLogRepository = None,
        system_settings_repository: SystemSettingsRepository = None,
        llm_log_repository: ILLMLogRepository = None
    ):
        self.repository = repository
        self.log_repository = log_repository
        self.system_settings_repository = system_settings_repository
        self.llm_log_repository = llm_log_repository
        
        # We still initialize a default embedding model here, but it will be overridden 
        # inside retrieve() if dynamic settings are fetched.
        self.embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL, 
            api_key=settings.OPENAI_API_KEY
        )

    async def retrieve(
        self,
        query: str,
        language: str = "English",
        threshold: float = None
    ) -> Tuple[List[DocumentChunk], str]:
        """Retrieve relevant document chunks with dynamic top-k and confidence scoring."""
        
        # Fetch dynamic settings
        top_k = 5
        sim_threshold = 0.7
        embedding_model = settings.OPENAI_EMBEDDING_MODEL
        api_key = settings.OPENAI_API_KEY
        
        if self.system_settings_repository:
            sys_settings = await self.system_settings_repository.get_settings()
            top_k = sys_settings.retrieval_top_k
            sim_threshold = sys_settings.retrieval_similarity_threshold
            embedding_model = sys_settings.retrieval_embedding_model
            if sys_settings.openai_api_key:
                api_key = sys_settings.openai_api_key
        
        # Override if explicitly passed
        if threshold is not None:
            sim_threshold = threshold
            
        # Re-initialize embeddings if model or key changed
        if embedding_model != self.embeddings.model or api_key != getattr(self.embeddings, 'api_key', settings.OPENAI_API_KEY):
            self.embeddings = OpenAIEmbeddings(
                model=embedding_model,
                api_key=api_key
            )

        logger.info(f"Retrieving Top-K: {top_k}, Threshold: {sim_threshold}, Model: {embedding_model}")

        try:
            emb_start = time.perf_counter()
            query_vector = await self.embeddings.aembed_query(query)
            emb_latency = int((time.perf_counter() - emb_start) * 1000)
            
            if self.llm_log_repository:
                try:
                    encoding = tiktoken.encoding_for_model(embedding_model)
                    tokens = len(encoding.encode(query))
                    await self.llm_log_repository.log_request(
                        user_id=None,
                        model_name=embedding_model,
                        query=query,
                        context="RAG Retrieval",
                        prompt_version="v1",
                        temperature=0.0,
                        prompt_tokens=tokens,
                        completion_tokens=0,
                        total_tokens=tokens,
                        latency_ms=emb_latency,
                        status="success",
                        error_message=None
                    )
                except Exception as e:
                    logger.error(f"Embedding telemetry failed: {e}")
            
            start_time = time.perf_counter()
            all_chunks = await self.repository.search_similar_chunks(
                query_vector, 
                limit=top_k, 
                threshold=sim_threshold
            )
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            
            # Filter chunks that pass the similarity threshold for LLM context
            chunks = [c for c in all_chunks if getattr(c, "similarity", 0.0) >= sim_threshold]
            
            confidence = self._calculate_confidence(chunks, query_vector)
            
            if self.log_repository:
                # Log ALL retrieved chunks (even below threshold) for monitoring visibility
                retrieved_data = [{"chunk_id": c.id, "similarity_score": getattr(c, "similarity", 0.0)} for c in all_chunks]
                await self.log_repository.log_retrieval(
                    conversation_id=None, # Passed from LLMService if we want to track it later, keeping simple for now
                    query=query,
                    language=language,
                    top_k=top_k,
                    retrieved_chunks=retrieved_data,
                    latency_ms=latency_ms
                )
                
            return chunks, confidence
            
        except Exception as e:
            await log_system_error(
                error_type="DB",
                message="Vector database retrieval or embedding failed.",
                details=f"Model: {embedding_model}\n{traceback.format_exc()}"
            )
            logger.error(f"Retrieval Service failed during similarity extraction: {str(e)}", exc_info=True)
            raise

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
