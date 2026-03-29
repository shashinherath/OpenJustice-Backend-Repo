"""DocumentChunk ORM model — RAG core with pgvector embeddings."""
from datetime import datetime
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base


class DocumentChunk(Base):
    """A chunk of a document with its vector embedding for RAG retrieval."""

    __tablename__ = "document_chunks"

    __table_args__ = (
        CheckConstraint("chunk_index >= 0", name="valid_chunk_index"),
        CheckConstraint("chunk_size > 0", name="valid_chunk_size"),
        Index("idx_doc_chunks_doc_id", "document_id"),
        Index("idx_doc_chunks_lang", "language"),
        Index("idx_doc_chunks_embedding_model", "embedding_model"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(20), nullable=False, default="English")

    # Vector embedding (1536 dims — text-embedding-3-small)
    embedding: Mapped[list] = mapped_column(Vector(1536), nullable=False)

    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, nullable=True, default=dict
    )

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_total: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_size: Mapped[int] = mapped_column(Integer, nullable=False)

    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)
    embedding_version: Mapped[str] = mapped_column(String(20), nullable=False)
    chunking_version: Mapped[str] = mapped_column(
        String(20), nullable=False, default="v1"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="chunks")  # type: ignore[name-defined]
    retrieved_in: Mapped[list["RetrievedDocument"]] = relationship("RetrievedDocument", back_populates="document_chunk", cascade="all, delete-orphan")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<DocumentChunk id={self.id} doc_id={self.document_id} idx={self.chunk_index}>"
