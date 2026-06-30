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
                    id=d.id,
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

    async def upload_and_save_dataset(self, file) -> str:
        import json
        import csv
        import io
        from app.infrastructure.models.research import EvaluationDataset, EvaluationDatasetItem as DbEvaluationDatasetItem
        
        content = await file.read()
        items_data = []
        filename = file.filename
        
        if filename.endswith(".json") or filename.endswith(".jsonl"):
            try:
                # Handle JSON array or JSONL
                if filename.endswith(".json"):
                    items_data = json.loads(content.decode('utf-8'))
                else:
                    lines = content.decode('utf-8').strip().split('\n')
                    items_data = [json.loads(line) for line in lines]
            except Exception as e:
                logger.error(f"Error parsing JSON: {e}")
                raise ValueError("Invalid JSON format")
        elif filename.endswith(".csv"):
            try:
                stream = io.StringIO(content.decode('utf-8'))
                reader = csv.DictReader(stream)
                items_data = list(reader)
            except Exception as e:
                logger.error(f"Error parsing CSV: {e}")
                raise ValueError("Invalid CSV format")
        else:
            raise ValueError("Unsupported file format. Use .json, .jsonl or .csv")
            
        if not items_data:
            raise ValueError("Dataset is empty")
            
        dataset = EvaluationDataset(
            name=filename.split(".")[0],
            version="v1.0",
            samples=len(items_data),
            split="100/0/0",
            last_run="Never",
            status="Ready"
        )
        dataset = await self.research_repository.create_evaluation_dataset(dataset)
        
        db_items = []
        for item in items_data:
            # handle lowercase and uppercase keys gracefully
            keys = {k.lower(): k for k in item.keys()}
            
            query = item.get(keys.get('query', 'query'), '')
            if not query:
                continue
                
            ground_truth = item.get(keys.get('ground_truth_answer', 'ground_truth_answer'), '')
            if not ground_truth:
                ground_truth = item.get(keys.get('answer', 'answer'), '')
                
            golden_context = item.get(keys.get('golden_context', 'golden_context'), '')
            if not golden_context:
                golden_context = item.get(keys.get('context', 'context'), '')
                
            db_item = DbEvaluationDatasetItem(
                dataset_id=dataset.id,
                query=query,
                ground_truth_answer=ground_truth,
                golden_context=golden_context
            )
            db_items.append(db_item)
            
        if db_items:
            await self.research_repository.create_dataset_items(db_items)
            
        # Update samples count in case some were skipped
        dataset.samples = len(db_items)
        await self.research_repository.update_dataset_status(dataset.id, "Ready", last_run="Never")
        return dataset.id
        
    async def trigger_evaluation(self, dataset_id: str):
        from app.application.services.dataset_evaluation_service import background_evaluate_dataset
        import asyncio
        asyncio.create_task(background_evaluate_dataset(dataset_id))

    async def delete_dataset(self, dataset_id: str) -> bool:
        return await self.research_repository.delete_evaluation_dataset(dataset_id)

