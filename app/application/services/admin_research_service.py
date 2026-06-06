import logging
from app.infrastructure.repositories.research_repository import ResearchRepository
from app.presentation.schemas.admin_schema import AdminResearchMetricsResponse, ResearchMetricItem, EvaluationDatasetItem, ExperimentNoteItem

logger = logging.getLogger(__name__)

class AdminResearchService:
    def __init__(self, research_repository: ResearchRepository):
        self.research_repository = research_repository

    async def get_research_metrics(self) -> AdminResearchMetricsResponse:
        metrics = await self.research_repository.get_metrics()
        datasets = await self.research_repository.get_datasets()
        notes = await self.research_repository.get_notes()

        # Deduplicate metrics by label to only show the latest
        latest_metrics = {}
        for m in metrics:
            if m.label not in latest_metrics:
                latest_metrics[m.label] = m

        return AdminResearchMetricsResponse(
            metrics=[
                ResearchMetricItem(
                    label=m.label,
                    value=m.value,
                    note=m.note,
                    trend=m.trend
                ) for m in latest_metrics.values()
            ],
            datasets=[
                EvaluationDatasetItem(
                    name=d.name,
                    version=d.version,
                    samples=d.samples,
                    split=d.split,
                    lastRun=d.last_run,
                    status=d.status
                ) for d in datasets
            ],
            experiment_notes=[
                ExperimentNoteItem(
                    title=n.title,
                    description=n.description
                ) for n in notes
            ]
        )
