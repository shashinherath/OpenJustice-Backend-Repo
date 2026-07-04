from sqlalchemy import String, Boolean, JSON, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base

class SystemSettings(Base):
    """System-wide configuration settings."""

    __tablename__ = "system_settings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    enabled_languages: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    default_language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    translation_pipeline_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # AI Configuration Fields
    ai_model_name: Mapped[str] = mapped_column(String(50), default="gpt-4o-mini", nullable=False)
    ai_temperature: Mapped[float] = mapped_column(Float, default=0.2, nullable=False)
    ai_max_tokens: Mapped[int] = mapped_column(Integer, default=1200, nullable=False)
    ai_top_p: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    ai_frequency_penalty: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Retrieval Configuration Fields
    retrieval_top_k: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    retrieval_similarity_threshold: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    retrieval_embedding_model: Mapped[str] = mapped_column(String(50), default="text-embedding-3-large", nullable=False)
    retrieval_chunk_size: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    retrieval_chunk_overlap: Mapped[int] = mapped_column(Integer, default=200, nullable=False)

    # Security Configuration Fields
    jwt_expiry_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    prompt_validation_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    account_lockout_threshold: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    # Integration Fields
    openai_api_key: Mapped[str] = mapped_column(String(255), nullable=True)
    twilio_account_sid: Mapped[str] = mapped_column(String(255), nullable=True)
    twilio_auth_token: Mapped[str] = mapped_column(String(255), nullable=True)
    whatsapp_phone_number: Mapped[str] = mapped_column(String(50), nullable=True)
    web_socket_url: Mapped[str] = mapped_column(String(255), nullable=True)
