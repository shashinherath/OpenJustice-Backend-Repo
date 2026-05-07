from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.document_repository import IDocumentRepository
from app.infrastructure.models.document import Document
from app.infrastructure.models.document_chunk import DocumentChunk


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

    async def get_total_count(self) -> int:
        result = await self.session.execute(select(func.count(Document.id)))
        return result.scalar_one_or_none() or 0

    async def delete(self, document_id: UUID) -> bool:
        document = await self.get_by_id(document_id)
        if document:
            await self.session.delete(document)
            await self.session.commit()
            return True
        return False

    async def update_status(self, document_id: UUID, status: str) -> Optional[Document]:
        document = await self.get_by_id(document_id)
        if document:
            document.status = status
            await self.session.commit()
            await self.session.refresh(document)
        return document

    async def save_chunks(self, chunks: List[DocumentChunk]) -> None:
        self.session.add_all(chunks)
        await self.session.commit()

    async def search_similar_chunks(self, query_embedding: list[float], limit: int = 5, threshold: float = 0.7) -> List[DocumentChunk]:
        """
        Uses pgvector's cosine_distance mapper to return the closest chunks.
        Lower distance means more similar for cosine distance natively in pgvector.
        A threshold of 0.7 means cosine distance must be < 0.3.
        """
        max_distance = 1.0 - threshold
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.embedding.cosine_distance(query_embedding) < max_distance)
            .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
