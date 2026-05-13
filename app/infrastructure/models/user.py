"""User ORM model."""
from datetime import datetime
import uuid as uuid_module
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.user_session import UserSession
    from app.infrastructure.models.conversation import Conversation
    from app.infrastructure.models.llm_request import LLMRequest
    from app.infrastructure.models.audio_request import AudioRequest
    from app.infrastructure.models.audit_log import AuditLog


class User(Base):
    """User database model."""

    __tablename__ = "users"

    id: Mapped[uuid_module.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid_module.uuid4)
    
    first_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )
    phone_number: Mapped[Optional[str]] = mapped_column(
        String(20), unique=True, nullable=True, index=True
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="user")
    preferred_language: Mapped[str] = mapped_column(
        String(10), nullable=False, default="en"
    )
    is_active: Mapped[bool] = mapped_column(
        nullable=False, default=True
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
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
    sessions: Mapped[list["UserSession"]] = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )
    llm_requests: Mapped[list["LLMRequest"]] = relationship(
        "LLMRequest", back_populates="user"
    )
    audio_requests: Mapped[list["AudioRequest"]] = relationship(
        "AudioRequest", back_populates="user"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="user"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id}>"
