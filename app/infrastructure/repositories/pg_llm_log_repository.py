import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.interfaces.llm_log_repository import ILLMLogRepository
from app.infrastructure.models.llm_request import LLMRequest
from app.infrastructure.models.llm_response import LLMResponse

class PgLLMLogRepository(ILLMLogRepository):
    """PostgreSQL implementation of LLM Traceability."""

    def __init__(self, session: AsyncSession):
        self.session = session

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
        req = LLMRequest(
            user_id=user_id,
            model_name=model_name,
            prompt_version=prompt_version,
            temperature=temperature,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            status=status,
            error_message=error_message
        )
        self.session.add(req)
        await self.session.flush()
        return req.id

    async def log_response(
        self,
        llm_request_id: uuid.UUID,
        response_text: str,
        confidence_level: str | None
    ) -> None:
        resp = LLMResponse(
            llm_request_id=llm_request_id,
            response_text=response_text,
            confidence_level=confidence_level
        )
        self.session.add(resp)
        await self.session.commit()

    async def get_error_count(self) -> int:
        from sqlalchemy import select, func
        result = await self.session.execute(
            select(func.count(LLMRequest.id)).where(LLMRequest.status == 'error')
        )
        return result.scalar_one_or_none() or 0
