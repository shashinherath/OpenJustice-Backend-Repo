"""SecurityEvent ORM model."""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, String, func, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
import uuid as uuid_module

from app.infrastructure.db.base import Base

class SecurityEvent(Base):
    """Security events and alerts."""

    __tablename__ = "security_events"

    __table_args__ = (
        Index("idx_security_events_created", "created_at"),
        Index("idx_security_events_area", "area"),
        Index("idx_security_events_severity", "severity"),
    )

    id: Mapped[uuid_module.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid_module.uuid4)
    area: Mapped[str] = mapped_column(String(100), nullable=False) # e.g., "Prompt Injection", "Failed Logins"
    source: Mapped[str] = mapped_column(String(100), nullable=False) # e.g., "Web chat client", "Admin portal"
    detail: Mapped[str] = mapped_column(String(500), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False) # "Critical", "High", "Medium", "Low"
    is_priority: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<SecurityEvent id={self.id} area={self.area} severity={self.severity}>"
