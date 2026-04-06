"""UserSession ORM model."""
from datetime import datetime
import uuid as uuid_module
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base


class UserSession(Base):
    """Tracks active user sessions across channels."""

    __tablename__ = "user_sessions"

    id: Mapped[uuid_module.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid_module.uuid4)
    user_id: Mapped[Optional[uuid_module.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    session_token: Mapped[uuid_module.UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False
    )
    channel: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True  # web / whatsapp / voice
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="sessions")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<UserSession id={self.id} user_id={self.user_id} channel={self.channel}>"
