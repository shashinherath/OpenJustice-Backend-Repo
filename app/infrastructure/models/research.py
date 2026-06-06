from sqlalchemy import Column, String, Float, Integer, DateTime
import uuid
from datetime import datetime

from app.infrastructure.db.base import Base

class ResearchMetric(Base):
    __tablename__ = "research_metrics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    label = Column(String(100), nullable=False)
    value = Column(String(50), nullable=False)
    note = Column(String(255), nullable=True)
    trend = Column(String(20), nullable=False) # 'up', 'down', 'neutral'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class EvaluationDataset(Base):
    __tablename__ = "evaluation_datasets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    samples = Column(Integer, nullable=False)
    split = Column(String(50), nullable=False)
    last_run = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False) # 'Ready', 'Running', 'Needs Refresh'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class ExperimentNote(Base):
    __tablename__ = "experiment_notes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
