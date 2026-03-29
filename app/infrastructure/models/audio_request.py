"""AudioRequest ORM model — voice AI processing."""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base


class AudioRequest(Base):
    """Records STT/TTS audio processing requests."""

    __tablename__ = "audio_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    audio_type: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True  # stt / tts
    )
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audio_requests")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<AudioRequest id={self.id} type={self.audio_type} lang={self.language}>"
