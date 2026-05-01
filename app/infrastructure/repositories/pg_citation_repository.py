import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.interfaces.citation_repository import ICitationRepository
from app.infrastructure.models.citation import Citation

class PgCitationRepository(ICitationRepository):
    """PostgreSQL implementation of Citation Tracking."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_citations(
        self,
        message_id: uuid.UUID,
        document_ids: List[uuid.UUID]
    ) -> None:
        # Deduplicate to prevent overlapping citations
        unique_docs = list(set(document_ids))
        
        for doc_id in unique_docs:
            citation = Citation(
                message_id=message_id,
                document_id=doc_id
            )
            self.session.add(citation)
            
        if unique_docs:
            await self.session.commit()
