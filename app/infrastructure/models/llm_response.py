"""LLMResponse ORM model."""
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base


class LLMResponse(Base):
    """Stores the text output from an LLM call."""

    __tablename__ = "llm_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    llm_request_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("llm_requests.id", ondelete="CASCADE"),
        nullable=True,
    )
    response_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Relationships
    llm_request: Mapped[Optional["LLMRequest"]] = relationship("LLMRequest", back_populates="responses")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<LLMResponse id={self.id} request_id={self.llm_request_id}>"
