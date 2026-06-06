"""AIEvaluation ORM model — stores AI evaluation metrics."""
from datetime import datetime
import uuid as uuid_module

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class AIEvaluation(Base):
    """Stores the model-level evaluation metrics such as accuracy, hallucination rate, and token consumption."""

    __tablename__ = "ai_evaluations"

    id: Mapped[uuid_module.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid_module.uuid4)
    evaluation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    hallucination_rate: Mapped[float] = mapped_column(Float, nullable=False)
    avg_tokens: Mapped[int] = mapped_column(Integer, nullable=False)

    def __repr__(self) -> str:
        return f"<AIEvaluation id={self.id} model={self.model_name} accuracy={self.accuracy}>"
