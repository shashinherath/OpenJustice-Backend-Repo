import logging
import asyncio
from typing import List, Tuple
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.repositories.research_repository import ResearchRepository
from app.infrastructure.repositories.system_settings_repository import SystemSettingsRepository
from app.application.services.retrieval_service import RetrievalService
from app.infrastructure.external.openai_client import OpenAIClient
from app.application.services.llm_as_a_judge_service import LLMAsAJudgeService
from app.infrastructure.repositories.document_repository import DocumentRepository
from app.infrastructure.repositories.pg_retrieval_log_repository import PgRetrievalLogRepository
from app.infrastructure.models.research import ResearchMetric

logger = logging.getLogger(__name__)

# Lightweight BLEU (Unigram overlap)
def compute_lightweight_bleu(reference: str, hypothesis: str) -> float:
    ref_tokens = set(reference.lower().split())
    hyp_tokens = set(hypothesis.lower().split())
    if not hyp_tokens or not ref_tokens:
        return 0.0
    overlap = ref_tokens.intersection(hyp_tokens)
    return len(overlap) / len(hyp_tokens)

# Lightweight ROUGE-L (Longest Common Subsequence length / reference length)
def compute_lightweight_rouge_l(reference: str, hypothesis: str) -> float:
    def lcs(X, Y):
        m = len(X)
        n = len(Y)
        L = [[0] * (n + 1) for i in range(m + 1)]
        for i in range(m + 1):
            for j in range(n + 1):
                if i == 0 or j == 0:
                    L[i][j] = 0
                elif X[i-1] == Y[j-1]:
                    L[i][j] = L[i-1][j-1] + 1
                else:
                    L[i][j] = max(L[i-1][j], L[i][j-1])
        return L[m][n]
    
    ref_tokens = reference.lower().split()
    hyp_tokens = hypothesis.lower().split()
    if not ref_tokens:
        return 0.0
    
    lcs_len = lcs(ref_tokens, hyp_tokens)
    return lcs_len / len(ref_tokens)
    
# Context recall (do golden context strings appear in retrieved chunks)
def compute_context_recall(golden_context: str, retrieved_context: str) -> float:
    if not golden_context:
        return 1.0 # If no golden context, assume recall is 100%
    golden_tokens = set(golden_context.lower().split())
    retrieved_tokens = set(retrieved_context.lower().split())
    if not golden_tokens:
        return 1.0
    overlap = golden_tokens.intersection(retrieved_tokens)
    return len(overlap) / len(golden_tokens)

class DatasetEvaluationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.research_repo = ResearchRepository(session)
        self.sys_repo = SystemSettingsRepository(session)
        self.doc_repo = DocumentRepository(session)
        self.retrieval_log_repo = PgRetrievalLogRepository(session)
        self.retrieval_service = RetrievalService(self.doc_repo, self.retrieval_log_repo, self.sys_repo)
        self.openai_client = OpenAIClient(self.sys_repo)
        self.judge_service = LLMAsAJudgeService(self.openai_client)

    async def evaluate_dataset(self, dataset_id: str):
        try:
            logger.info(f"Starting evaluation for dataset {dataset_id}")
            await self.research_repo.update_dataset_status(dataset_id, "Running")
            
            items = await self.research_repo.get_dataset_items(dataset_id)
            if not items:
                logger.warning(f"No items found for dataset {dataset_id}")
                await self.research_repo.update_dataset_status(dataset_id, "Ready", last_run=datetime.utcnow().strftime("%Y-%m-%d"))
                return
            
            total_bleu = 0.0
            total_rouge = 0.0
            total_context_recall = 0.0
            total_faithfulness = 0.0
            total_relevance = 0.0
            
            for item in items:
                # 1. Retrieve
                chunks, conf = await self.retrieval_service.retrieve(query=item.query)
                retrieved_context = "\n".join([c.content for c in chunks]) if chunks else ""
                
                # 2. Generate
                prompt = f"Answer the query based on context.\nQuery: {item.query}\nContext: {retrieved_context}"
                messages = [{"role": "user", "content": prompt}]
                response_text = await self.openai_client.generate_response(messages)
                
                # 3. Evaluate Metrics
                total_bleu += compute_lightweight_bleu(item.ground_truth_answer, response_text)
                total_rouge += compute_lightweight_rouge_l(item.ground_truth_answer, response_text)
                total_context_recall += compute_context_recall(item.golden_context or "", retrieved_context)
                
                faith = await self.judge_service.evaluate_faithfulness(item.query, retrieved_context, response_text)
                rel = await self.judge_service.evaluate_answer_relevance(item.query, response_text)
                
                total_faithfulness += faith
                total_relevance += rel
            
            count = len(items)
            avg_bleu = total_bleu / count
            avg_rouge = total_rouge / count
            avg_context_recall = total_context_recall / count
            avg_faithfulness = total_faithfulness / count
            avg_relevance = total_relevance / count
            ragas_score = (avg_faithfulness + avg_relevance) / 2
            
            def generate_metric(label, value, note):
                trend = "up" if value > 0.8 else "down" if value < 0.6 else "neutral"
                return ResearchMetric(label=label, value=str(round(value, 2)), note=note, trend=trend)
                
            metrics = [
                generate_metric("Faithfulness", avg_faithfulness, "Groundedness against retrieved context"),
                generate_metric("Context Precision", avg_relevance, "Relevant chunks among retrieved context"),
                generate_metric("RAGAS Score", ragas_score, "Composite retrieval-generation score"),
                generate_metric("Context Recall", avg_context_recall, "Coverage of required evidence"),
                generate_metric("BLEU", avg_bleu, "n-gram overlap with references"),
                generate_metric("ROUGE-L", avg_rouge, "Longest common subsequence overlap")
            ]
            
            for m in metrics:
                await self.research_repo.add_metric(m)
                
            await self.research_repo.update_dataset_status(dataset_id, "Ready", last_run=datetime.utcnow().strftime("%Y-%m-%d"))
            logger.info(f"Finished evaluation for dataset {dataset_id}")
            
        except Exception as e:
            logger.error(f"Error evaluating dataset {dataset_id}: {e}")
            await self.research_repo.update_dataset_status(dataset_id, "Needs Refresh")

async def background_evaluate_dataset(dataset_id: str):
    from app.infrastructure.db.base import get_db
    async for session in get_db():
        service = DatasetEvaluationService(session)
        await service.evaluate_dataset(dataset_id)
        # We only need to run this once per background task with one session
        try:
            await session.commit()
        except Exception:
            await session.rollback()
        break
