from abc import ABC, abstractmethod
from typing import Optional, Tuple

class ISemanticCacheRepository(ABC):
    """Repository interface for Semantic Caching of LLM outputs."""

    @abstractmethod
    async def get_similar_response(
        self, query_embedding: list[float], similarity_threshold: float = 0.95
    ) -> Optional[str]:
        """
        Retrieves a semantically similar response from the cache if the similarity 
        score is above the provided threshold.

        Args:
            query_embedding: The vector embedding of the user's query.
            similarity_threshold: The minimum cosine similarity required to hit the cache.

        Returns:
            The cached response text if a match is found, else None.
        """
        pass

    @abstractmethod
    async def set_response(self, query_text: str, query_embedding: list[float], response_text: str) -> None:
        """
        Stores a query and its generated response into the semantic cache.

        Args:
            query_text: The original user query.
            query_embedding: The vector embedding of the user query.
            response_text: The generated LLM response to be cached.
        """
        pass
