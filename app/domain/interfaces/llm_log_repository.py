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
        query: str | None,
        context: str | None,
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

    @abstractmethod
    async def get_error_count(self) -> int:
        """Counts the total number of errors."""
        pass

    @abstractmethod
    async def get_logs(self, skip: int = 0, limit: int = 100) -> tuple[int, list]:
        """Gets a paginated list of LLM requests."""
        pass

    @abstractmethod
    async def get_stats(self) -> dict:
        """Returns total counts by status, sum of tokens, and avg latency."""
        pass

    @abstractmethod
    async def update_log_status(self, log_id: uuid.UUID, status: str) -> bool:
        """Updates the status of a specific log."""
        pass

    @abstractmethod
    async def delete_log(self, log_id: uuid.UUID) -> bool:
        """Deletes a specific log."""
        pass

    @abstractmethod
    async def get_responses_today_count(self) -> int:
        """Count responses generated today."""
        pass

    @abstractmethod
    async def get_avg_response_time(self) -> float:
        """Calculate average response time."""
        pass
