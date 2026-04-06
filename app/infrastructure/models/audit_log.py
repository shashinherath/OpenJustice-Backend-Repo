"""AuditLog ORM model — compliance and security audit trail."""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
import uuid as uuid_module

from app.infrastructure.db.base import Base


class AuditLog(Base):
    """Immutable audit trail for user actions and system events."""

    __tablename__ = "audit_logs"

    __table_args__ = (
        Index("idx_audit_logs_user", "user_id"),
    )

    id: Mapped[uuid_module.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid_module.uuid4)
    user_id: Mapped[Optional[uuid_module.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), index=True)
    action: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    entity: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[Optional[uuid_module.UUID]] = mapped_column(Integer, nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} user_id={self.user_id} action={self.action}>"
