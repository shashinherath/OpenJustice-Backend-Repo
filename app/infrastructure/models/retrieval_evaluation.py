"""RetrievalEvaluation ORM model — stores offline benchmark metrics."""
from datetime import datetime
import uuid as uuid_module

from sqlalchemy import DateTime, Float, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class RetrievalEvaluation(Base):
    """Stores the precision and recall scores of scheduled offline retrieval benchmarks."""

    __tablename__ = "retrieval_evaluations"

    id: Mapped[uuid_module.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid_module.uuid4)
    evaluation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    recall_at_5: Mapped[float] = mapped_column(Float, nullable=False)
    precision_at_5: Mapped[float] = mapped_column(Float, nullable=False)

    def __repr__(self) -> str:
        return f"<RetrievalEvaluation id={self.id} recall={self.recall_at_5} precision={self.precision_at_5}>"
