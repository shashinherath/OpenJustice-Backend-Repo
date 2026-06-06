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
        req = LLMRequest(
            user_id=user_id,
            model_name=model_name,
            query=query,
            context=context,
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

    async def get_logs(self, skip: int = 0, limit: int = 100) -> tuple[int, list]:
        from sqlalchemy import select, func
        total_result = await self.session.execute(select(func.count(LLMRequest.id)))
        total = total_result.scalar_one_or_none() or 0
        
        result = await self.session.execute(
            select(LLMRequest).order_by(LLMRequest.created_at.desc()).offset(skip).limit(limit)
        )
        logs = list(result.scalars().all())
        return total, logs

    async def update_log_status(self, log_id: uuid.UUID, status: str) -> bool:
        from sqlalchemy import select
        result = await self.session.execute(select(LLMRequest).where(LLMRequest.id == log_id))
        log = result.scalar_one_or_none()
        if not log:
            return False
        log.status = status
        await self.session.commit()
        return True

    async def delete_log(self, log_id: uuid.UUID) -> bool:
        from sqlalchemy import select
        result = await self.session.execute(select(LLMRequest).where(LLMRequest.id == log_id))
        log = result.scalar_one_or_none()
        if not log:
            return False
        await self.session.delete(log)
        await self.session.commit()
        return True

    async def get_responses_today_count(self) -> int:
        from sqlalchemy import select, func, text
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(days=1)
        result = await self.session.execute(
            select(func.count(LLMRequest.id)).where(LLMRequest.created_at >= cutoff)
        )
        return result.scalar_one_or_none() or 0

    async def get_avg_response_time(self) -> float:
        from sqlalchemy import select, func
        result = await self.session.execute(
            select(func.avg(LLMRequest.latency_ms))
        )
        return result.scalar_one_or_none() or 0.0
