from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.infrastructure.models.research import ResearchMetric, EvaluationDataset, ExperimentNote, EvaluationDatasetItem

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

    async def create_evaluation_dataset(self, dataset: EvaluationDataset) -> EvaluationDataset:
        self.session.add(dataset)
        await self.session.flush()
        return dataset
        
    async def get_dataset_by_id(self, dataset_id: str) -> Optional[EvaluationDataset]:
        result = await self.session.execute(
            select(EvaluationDataset).where(EvaluationDataset.id == dataset_id)
        )
        return result.scalar_one_or_none()

    async def create_dataset_items(self, items: List[EvaluationDatasetItem]) -> None:
        self.session.add_all(items)
        await self.session.flush()

    async def get_dataset_items(self, dataset_id: str) -> List[EvaluationDatasetItem]:
        result = await self.session.execute(
            select(EvaluationDatasetItem).where(EvaluationDatasetItem.dataset_id == dataset_id)
        )
        return list(result.scalars().all())

    async def update_dataset_status(self, dataset_id: str, status: str, last_run: str = None) -> None:
        stmt = update(EvaluationDataset).where(EvaluationDataset.id == dataset_id).values(status=status)
        if last_run:
            stmt = stmt.values(last_run=last_run)
        await self.session.execute(stmt)
        await self.session.flush()

    async def delete_evaluation_dataset(self, dataset_id: str) -> bool:
        from sqlalchemy import delete
        # Delete items first since there is no strict CASCADE set up
        await self.session.execute(
            delete(EvaluationDatasetItem).where(EvaluationDatasetItem.dataset_id == dataset_id)
        )
        # Delete the dataset
        result = await self.session.execute(
            delete(EvaluationDataset).where(EvaluationDataset.id == dataset_id)
        )
        await self.session.flush()
        return result.rowcount > 0

