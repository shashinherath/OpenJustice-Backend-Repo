from app.domain.interfaces.document_repository import IDocumentRepository

class AdminKnowledgeService:
    def __init__(self, document_repo: IDocumentRepository):
        self.document_repo = document_repo

    async def get_knowledge_metrics(self) -> dict:
        records = await self.document_repo.get_knowledge_metrics()
        return {"records": records}
