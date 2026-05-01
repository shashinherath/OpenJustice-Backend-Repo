from abc import ABC, abstractmethod
import uuid
from typing import Optional

class ILLMLogRepository(ABC):
    """Interface for logging LLM API requests and responses."""

    @abstractmethod
    async def log_request(
        self,
        user_id: uuid.UUID | None,
        model_name: str,
        prompt_version: str | None,
        temperature: float,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        latency_ms: int,
        status: str,
        error_message: str | None
    ) -> uuid.UUID:
        """Logs the LLM Request and returns its ID."""
        pass

    @abstractmethod
    async def log_response(
        self,
        llm_request_id: uuid.UUID,
        response_text: str,
        confidence_level: str | None
    ) -> None:
        """Links the generated text output to the specific LLM request."""
        pass
