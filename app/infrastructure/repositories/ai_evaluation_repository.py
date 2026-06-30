"""Repository for accessing AIEvaluation records."""
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.ai_evaluation import AIEvaluation

class AIEvaluationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_latest_global_metrics(self) -> Optional[dict]:
        """Calculates global averages across all AI evaluations."""
        result = await self.session.execute(
            select(
                func.avg(AIEvaluation.accuracy).label("avg_accuracy"),
                func.avg(AIEvaluation.hallucination_rate).label("avg_hallucination_rate"),
                func.avg(AIEvaluation.avg_tokens).label("global_avg_tokens"),
            )
        )
        row = result.fetchone()
        if row and row.avg_accuracy is not None:
            return {
                "accuracy": round(row.avg_accuracy, 2),
                "hallucination_rate": round(row.avg_hallucination_rate, 2),
                "avg_tokens": int(row.global_avg_tokens)
            }
        return None

    async def get_recent_runs(self, limit: int = 5) -> List[AIEvaluation]:
        """Fetches the most recent distinct model runs."""
        result = await self.session.execute(
            select(AIEvaluation).order_by(AIEvaluation.evaluation_date.desc())
        )
        all_runs = result.scalars().all()
        
        distinct_runs = []
        seen_models = set()
        for run in all_runs:
            if run.model_name not in seen_models:
                distinct_runs.append(run)
                seen_models.add(run.model_name)
            if len(distinct_runs) >= limit:
                break
                
        return distinct_runs
