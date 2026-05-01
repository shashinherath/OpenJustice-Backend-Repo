from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.interfaces.semantic_cache_repository import ISemanticCacheRepository
from app.infrastructure.models.semantic_cache import SemanticCache

class PgVectorSemanticCacheRepository(ISemanticCacheRepository):
    """PostgreSQL pgvector implementation of the Semantic Cache Repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_similar_response(
        self, query_embedding: list[float], similarity_threshold: float = 0.95
    ) -> Optional[str]:
        """
        Finds a cached response using cosine similarity via pgvector.
        Cos distance is (1 - cosine similarity). So Cosine similarity > 0.95 
        means distance < 0.05.
        """
        distance_threshold = 1.0 - similarity_threshold

        # pgvector uses `<=>` for cosine distance
        query = (
            select(SemanticCache.response_text)
            .filter(SemanticCache.query_embedding.cosine_distance(query_embedding) < distance_threshold)
            .order_by(SemanticCache.query_embedding.cosine_distance(query_embedding))
            .limit(1)
        )

        result = await self.session.execute(query)
        cached_response = result.scalar_one_or_none()

        return cached_response

    async def set_response(self, query_text: str, query_embedding: list[float], response_text: str) -> None:
        """Saves a new query-response pair to the semantic cache."""
        cache_entry = SemanticCache(
            query_text=query_text,
            query_embedding=query_embedding,
            response_text=response_text
        )
        self.session.add(cache_entry)
        await self.session.commit()
