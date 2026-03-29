"""User ORM model."""
from datetime import datetime
import uuid as uuid_module
from typing import Optional

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class User(Base):
    """User database model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[uuid_module.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        unique=True,
        nullable=False,
        default=uuid_module.uuid4,
        index=True,
    )
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

    def __repr__(self) -> str:
        return f"<User id={self.id} uuid={self.uuid}>"
