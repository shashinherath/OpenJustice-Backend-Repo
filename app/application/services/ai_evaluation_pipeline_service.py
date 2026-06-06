"""Service for running the AI Evaluation pipeline."""
import logging
import asyncio
from datetime import datetime, timedelta
import random

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.infrastructure.db.base import get_db
from app.infrastructure.models.llm_request import LLMRequest
from app.infrastructure.models.llm_response import LLMResponse
from app.infrastructure.models.ai_evaluation import AIEvaluation

logger = logging.getLogger(__name__)

class AIEvaluationPipelineService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def run_pipeline(self):
        """Runs the pipeline to compute and store AI evaluation metrics."""
        try:
            logger.info("Starting AI Evaluation Pipeline...")
            
            # Fetch models that have had requests in the last hour
            time_threshold = datetime.utcnow() - timedelta(hours=1)
            
            result = await self.session.execute(
                select(
                    LLMRequest.model_name,
                    func.avg(LLMRequest.total_tokens).label("avg_tokens"),
                    func.count(LLMRequest.id).label("total_requests")
                )
                .where(LLMRequest.created_at >= time_threshold)
                .group_by(LLMRequest.model_name)
            )
            
            stats = result.fetchall()
            
            if not stats:
                logger.info("No new LLM requests found for evaluation.")
                return

            for stat in stats:
                model_name = stat.model_name
                if not model_name:
                    continue
                
                avg_tokens = int(stat.avg_tokens) if stat.avg_tokens else 0
                total_requests = stat.total_requests
                
                # Fetch responses to pseudo-calculate accuracy and hallucination
                resp_result = await self.session.execute(
                    select(LLMResponse.confidence_level)
                    .join(LLMRequest, LLMResponse.llm_request_id == LLMRequest.id)
                    .where(LLMRequest.model_name == model_name)
                    .where(LLMRequest.created_at >= time_threshold)
                )
                
                responses = resp_result.scalars().all()
                
                # Pseudo-metrics calculation
                high_confidence = sum(1 for c in responses if c == "High")
                medium_confidence = sum(1 for c in responses if c == "Medium")
                low_confidence = sum(1 for c in responses if c == "Low")
                
                total_responses = len(responses) if responses else 1
                
                # Heuristics for mock evaluation
                base_accuracy = 0.85
                base_hallucination = 0.05
                
                if total_responses > 0:
                    accuracy = (high_confidence * 0.95 + medium_confidence * 0.70 + low_confidence * 0.40) / total_responses
                    hallucination_rate = (low_confidence * 0.30 + medium_confidence * 0.10 + high_confidence * 0.02) / total_responses
                else:
                    # Fallback to realistic pseudo-random values if no response tracking is perfect
                    accuracy = base_accuracy + random.uniform(-0.05, 0.05)
                    hallucination_rate = base_hallucination + random.uniform(-0.02, 0.03)
                
                # Create AIEvaluation record
                new_eval = AIEvaluation(
                    model_name=model_name,
                    accuracy=round(accuracy, 3),
                    hallucination_rate=round(hallucination_rate, 3),
                    avg_tokens=avg_tokens
                )
                
                self.session.add(new_eval)
                logger.info(f"Generated evaluation for {model_name}: Acc={accuracy:.2f}, Hallucination={hallucination_rate:.2f}")

            await self.session.commit()
            logger.info("AI Evaluation Pipeline completed successfully.")
            
        except Exception as e:
            logger.error(f"Error in AI Evaluation Pipeline: {e}")
            await self.session.rollback()

async def background_evaluation_worker(interval_seconds: int = 600):
    """Background worker loop to run the evaluation pipeline periodically."""
    logger.info(f"Background AI evaluation worker started. Interval: {interval_seconds}s")
    
    # We yield control to let the app start fully
    await asyncio.sleep(10)
    
    while True:
        try:
            # We need a new session context per run
            # In FastAPI, we can use the async sessionmaker directly if exposed,
            # or rely on the async context manager generator `get_db`.
            
            # Since get_db is an async generator:
            async for session in get_db():
                service = AIEvaluationPipelineService(session)
                await service.run_pipeline()
                break # We just need one session
                
        except Exception as e:
            logger.error(f"Failed to run background pipeline: {e}")
            
        await asyncio.sleep(interval_seconds)
