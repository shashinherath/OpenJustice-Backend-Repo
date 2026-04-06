from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.document_repository import IDocumentRepository
from app.infrastructure.models.document import Document


class DocumentRepository(IDocumentRepository):
    """SQLAlchemy implementation of the document repository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, document: Document) -> Document:
        self.session.add(document)
        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def get_by_id(self, document_id: UUID) -> Optional[Document]:
        result = await self.session.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalars().first()

    async def list_documents(self, skip: int = 0, limit: int = 100) -> List[Document]:
        result = await self.session.execute(
            select(Document).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def delete(self, document_id: UUID) -> bool:
        document = await self.get_by_id(document_id)
        if document:
            await self.session.delete(document)
            await self.session.commit()
            return True
        return False
