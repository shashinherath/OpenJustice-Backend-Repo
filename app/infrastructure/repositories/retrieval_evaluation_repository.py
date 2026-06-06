from typing import List, Tuple, Dict
from sqlalchemy import select, func, text, cast, Integer
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.retrieval_evaluation import RetrievalEvaluation
from app.infrastructure.models.retrieved_document import RetrievedDocument

class RetrievalEvaluationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_latest_evaluation(self) -> RetrievalEvaluation | None:
        stmt = select(RetrievalEvaluation).order_by(RetrievalEvaluation.evaluation_date.desc()).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_similarity_distribution(self) -> List[Dict[str, int]]:
        # Group similarities into bins: <0.2, 0.2-0.4, 0.4-0.6, 0.6-0.8, 0.8-1.0
        # Since similarity is usually 0.0 to 1.0, we can multiply by 5, cast to int, and group by that.
        # But a more standard way for PostgreSQL is to use a case statement or width_bucket.
        # Let's do a simple case statement.
        
        stmt = text("""
            SELECT 
                CASE 
                    WHEN similarity_score < 0.2 THEN '0.0-0.2'
                    WHEN similarity_score < 0.4 THEN '0.2-0.4'
                    WHEN similarity_score < 0.6 THEN '0.4-0.6'
                    WHEN similarity_score < 0.8 THEN '0.6-0.8'
                    ELSE '0.8-1.0'
                END as bin_label,
                COUNT(*) as count
            FROM retrieved_documents
            WHERE similarity_score IS NOT NULL
            GROUP BY bin_label
            ORDER BY bin_label
        """)
        
        result = await self.db.execute(stmt)
        rows = result.fetchall()
        
        # Ensure all bins are present even if count is 0
        bins = {
            '0.0-0.2': 0,
            '0.2-0.4': 0,
            '0.4-0.6': 0,
            '0.6-0.8': 0,
            '0.8-1.0': 0
        }
        
        for row in rows:
            bins[row[0]] = row[1]
            
        # Return as sorted list of dicts
        return [
            {"bin_label": k, "count": v}
            for k, v in bins.items()
        ]
