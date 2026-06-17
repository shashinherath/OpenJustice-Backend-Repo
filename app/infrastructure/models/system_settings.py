from sqlalchemy import String, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base

class SystemSettings(Base):
    """System-wide configuration settings."""

    __tablename__ = "system_settings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    enabled_languages: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    default_language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    translation_pipeline_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
