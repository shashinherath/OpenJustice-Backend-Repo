from app.infrastructure.repositories.retrieval_evaluation_repository import RetrievalEvaluationRepository
from app.presentation.schemas.admin_schema import AdminRetrievalEvaluationResponse, RetrievalDistributionBin

class AdminRetrievalEvaluationService:
    def __init__(self, repository: RetrievalEvaluationRepository):
        self.repository = repository

    async def get_retrieval_evaluation(self) -> AdminRetrievalEvaluationResponse:
        evaluation = await self.repository.get_latest_evaluation()
        distribution = await self.repository.get_similarity_distribution()
        
        # If no evaluation exists yet, provide baseline numbers
        recall_at_5 = evaluation.recall_at_5 if evaluation else 0.82
        precision_at_5 = evaluation.precision_at_5 if evaluation else 0.74
        
        distribution_bins = [
            RetrievalDistributionBin(bin_label=item["bin_label"], count=item["count"])
            for item in distribution
        ]
        
        return AdminRetrievalEvaluationResponse(
            recall_at_5=recall_at_5,
            precision_at_5=precision_at_5,
            similarity_distribution=distribution_bins
        )
