"""LLMRequest ORM model — full LLM call traceability."""
from datetime import datetime
import uuid as uuid_module
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base


class LLMRequest(Base):
    """Records every LLM API call for research and cost traceability."""

    __tablename__ = "llm_requests"

    __table_args__ = (
        Index("idx_llm_requests_user", "user_id"),
    )

    id: Mapped[uuid_module.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid_module.uuid4)
    correlation_id: Mapped[Optional[uuid_module.UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    user_id: Mapped[Optional[uuid_module.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), index=True)

    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    temperature: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_tokens: Mapped[Optional[uuid_module.UUID]] = mapped_column(Integer, nullable=True)

    prompt_tokens: Mapped[Optional[uuid_module.UUID]] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[Optional[uuid_module.UUID]] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[Optional[uuid_module.UUID]] = mapped_column(Integer, nullable=True)

    latency_ms: Mapped[Optional[uuid_module.UUID]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="llm_requests")  # type: ignore[name-defined]
    responses: Mapped[list["LLMResponse"]] = relationship("LLMResponse", back_populates="llm_request", cascade="all, delete-orphan")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<LLMRequest id={self.id} model={self.model_name} status={self.status}>"
