"""RetrievalLog ORM model — RAG traceability."""
from datetime import datetime
import uuid as uuid_module
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base


class RetrievalLog(Base):
    """Logs each RAG retrieval query for traceability."""

    __tablename__ = "retrieval_logs"

    id: Mapped[uuid_module.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid_module.uuid4)
    correlation_id: Mapped[Optional[uuid_module.UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    conversation_id: Mapped[Optional[uuid_module.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    query: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    top_k: Mapped[Optional[uuid_module.UUID]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    retrieved_documents: Mapped[list["RetrievedDocument"]] = relationship(  # type: ignore[name-defined]
        "RetrievedDocument", back_populates="retrieval_log", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<RetrievalLog id={self.id} correlation_id={self.correlation_id}>"
