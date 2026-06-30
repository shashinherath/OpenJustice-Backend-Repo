"""Service for handling Admin AI Evaluation metrics."""
from app.infrastructure.repositories.ai_evaluation_repository import AIEvaluationRepository

class AdminAIEvaluationService:
    def __init__(self, ai_evaluation_repo: AIEvaluationRepository):
        self.ai_evaluation_repo = ai_evaluation_repo

    async def get_ai_evaluation_metrics(self) -> dict:
        """Fetch AI evaluation metrics and recent runs for the admin dashboard."""
        
        metrics = await self.ai_evaluation_repo.get_latest_global_metrics()
        runs = await self.ai_evaluation_repo.get_recent_runs(limit=5)
        
        if not metrics:
            metrics = {
                "accuracy": 0.0,
                "hallucination_rate": 0.0,
                "avg_tokens": 0
            }
            
        formatted_runs = [
            {
                "model": run.model_name,
                "accuracy": run.accuracy,
                "tokens": run.avg_tokens,
                "date": run.evaluation_date.isoformat() if run.evaluation_date else ""
            }
            for run in runs
        ]
        
        return {
            "accuracy": metrics["accuracy"],
            "hallucination_rate": metrics["hallucination_rate"],
            "avg_tokens": metrics["avg_tokens"],
            "recent_model_runs": formatted_runs
        }
