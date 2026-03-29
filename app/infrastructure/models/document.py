"""Document ORM model."""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base


class Document(Base):
    """A legal document stored in the system."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    document_type: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True  # Act / Case / Regulation
    )
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    storage_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    published_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    chunks: Mapped[list["DocumentChunk"]] = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")  # type: ignore[name-defined]
    citations: Mapped[list["Citation"]] = relationship("Citation", back_populates="document")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<Document id={self.id} title={self.title!r}>"
