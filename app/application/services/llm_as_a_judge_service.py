import logging
from typing import Dict
from app.domain.interfaces.llm_client import ILLMClient
from app.config import settings

logger = logging.getLogger(__name__)

class LLMAsAJudgeService:
    """Service to evaluate RAG responses using an LLM-as-a-judge."""

    def __init__(self, llm_client: ILLMClient):
        self.llm_client = llm_client

    async def evaluate_faithfulness(self, query: str, context: str, response: str) -> float:
        """Evaluates how faithful the response is to the retrieved context."""
        if not context or not response:
            return 0.0

        prompt = (
            "You are an impartial judge evaluating a RAG (Retrieval-Augmented Generation) system.\n"
            "Your task is to determine if the RESPONSE is FAITHFUL to the CONTEXT.\n"
            "A response is faithful if all claims made in the response can be inferred from the context.\n"
            "It is NOT faithful if it includes hallucinations or external information not present in the context.\n\n"
            f"CONTEXT:\n{context}\n\n"
            f"RESPONSE:\n{response}\n\n"
            "Output ONLY a single floating point number between 0.0 and 1.0 representing the faithfulness score. 1.0 means perfectly faithful. Do not output any other text."
        )

        messages = [
            {"role": "system", "content": "You are an expert evaluator of AI systems."},
            {"role": "user", "content": prompt}
        ]

        try:
            score_text = await self.llm_client.generate_response(messages, temperature=0.0)
            score = float(score_text.strip())
            return min(max(score, 0.0), 1.0)
        except Exception as e:
            logger.error(f"Failed to evaluate faithfulness: {e}")
            return 0.0

    async def evaluate_answer_relevance(self, query: str, response: str) -> float:
        """Evaluates how relevant the response is to the user's query."""
        if not query or not response:
            return 0.0

        prompt = (
            "You are an impartial judge evaluating a RAG (Retrieval-Augmented Generation) system.\n"
            "Your task is to determine if the RESPONSE is RELEVANT to the user's QUERY.\n"
            "A response is relevant if it directly answers the query without going off-topic or providing unnecessary tangential information.\n\n"
            f"QUERY:\n{query}\n\n"
            f"RESPONSE:\n{response}\n\n"
            "Output ONLY a single floating point number between 0.0 and 1.0 representing the relevance score. 1.0 means perfectly relevant. Do not output any other text."
        )

        messages = [
            {"role": "system", "content": "You are an expert evaluator of AI systems."},
            {"role": "user", "content": prompt}
        ]

        try:
            score_text = await self.llm_client.generate_response(messages, temperature=0.0)
            score = float(score_text.strip())
            return min(max(score, 0.0), 1.0)
        except Exception as e:
            logger.error(f"Failed to evaluate answer relevance: {e}")
            return 0.0
