"""Citation ORM model — anti-hallucination source tracking."""
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
import uuid as uuid_module

from app.infrastructure.db.base import Base


class Citation(Base):
    """Links an assistant message to the source document that supported it."""

    __tablename__ = "citations"

    id: Mapped[uuid_module.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid_module.uuid4)
    message_id: Mapped[Optional[uuid_module.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[Optional[uuid_module.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("documents.id"), index=True)
    section_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    message: Mapped[Optional["Message"]] = relationship("Message", back_populates="citations")  # type: ignore[name-defined]
    document: Mapped[Optional["Document"]] = relationship("Document", back_populates="citations")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<Citation id={self.id} message_id={self.message_id} doc_id={self.document_id}>"
