"""LLMResponse ORM model."""
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
import uuid as uuid_module

from app.infrastructure.db.base import Base


class LLMResponse(Base):
    """Stores the text output from an LLM call."""

    __tablename__ = "llm_responses"

    id: Mapped[uuid_module.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid_module.uuid4)
    llm_request_id: Mapped[Optional[uuid_module.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("llm_requests.id", ondelete="CASCADE"), index=True)
    response_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Relationships
    llm_request: Mapped[Optional["LLMRequest"]] = relationship("LLMRequest", back_populates="responses")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<LLMResponse id={self.id} request_id={self.llm_request_id}>"
