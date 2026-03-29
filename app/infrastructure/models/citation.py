"""Citation ORM model — anti-hallucination source tracking."""
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base


class Citation(Base):
    """Links an assistant message to the source document that supported it."""

    __tablename__ = "citations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=True,
    )
    document_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("documents.id"),
        nullable=True,
    )
    section_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    message: Mapped[Optional["Message"]] = relationship("Message", back_populates="citations")  # type: ignore[name-defined]
    document: Mapped[Optional["Document"]] = relationship("Document", back_populates="citations")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<Citation id={self.id} message_id={self.message_id} doc_id={self.document_id}>"
