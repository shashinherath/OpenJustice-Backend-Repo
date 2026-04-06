"""RetrievedDocument ORM model — links retrieval logs to specific chunks."""
from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
import uuid as uuid_module

from app.infrastructure.db.base import Base


class RetrievedDocument(Base):
    """Records which document chunks were returned for a retrieval query."""

    __tablename__ = "retrieved_documents"

    id: Mapped[uuid_module.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid_module.uuid4)
    retrieval_log_id: Mapped[Optional[uuid_module.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("retrieval_logs.id", ondelete="CASCADE"), index=True)
    document_chunk_id: Mapped[Optional[uuid_module.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("document_chunks.id", ondelete="CASCADE"), index=True)
    similarity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    retrieval_log: Mapped[Optional["RetrievalLog"]] = relationship("RetrievalLog", back_populates="retrieved_documents")  # type: ignore[name-defined]
    document_chunk: Mapped[Optional["DocumentChunk"]] = relationship("DocumentChunk", back_populates="retrieved_in")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<RetrievedDocument id={self.id} score={self.similarity_score}>"
