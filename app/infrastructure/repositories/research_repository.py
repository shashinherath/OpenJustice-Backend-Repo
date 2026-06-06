from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.infrastructure.models.research import ResearchMetric, EvaluationDataset, ExperimentNote

class ResearchRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_metrics(self) -> List[ResearchMetric]:
        result = await self.session.execute(
            select(ResearchMetric).order_by(ResearchMetric.created_at.desc()).limit(20)
        )
        return list(result.scalars().all())

    async def get_datasets(self) -> List[EvaluationDataset]:
        result = await self.session.execute(
            select(EvaluationDataset).order_by(EvaluationDataset.created_at.desc()).limit(10)
        )
        return list(result.scalars().all())

    async def get_notes(self) -> List[ExperimentNote]:
        result = await self.session.execute(
            select(ExperimentNote).order_by(ExperimentNote.created_at.desc()).limit(10)
        )
        return list(result.scalars().all())
    
    async def add_metric(self, metric: ResearchMetric) -> ResearchMetric:
        self.session.add(metric)
        return metric
