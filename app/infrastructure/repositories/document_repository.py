from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, delete
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

    async def list_documents(
        self,
        skip: int = 0,
        limit: int = 25,
        search_query: Optional[str] = None,
        language: Optional[str] = None,
        status: Optional[str] = None,
        collection_id: Optional[str] = None,
        letter: Optional[str] = None
    ) -> List[Document]:
        stmt = select(Document)
        
        if search_query:
            stmt = stmt.where(Document.title.ilike(f"%{search_query}%"))
        if language:
            stmt = stmt.where(Document.language == language)
        if status:
            stmt = stmt.where(Document.status == status)
        if collection_id:
            stmt = stmt.where(Document.collection_id == collection_id)
        if letter:
            stmt = stmt.where(Document.title.ilike(f"{letter}%"))
            
        stmt = stmt.order_by(Document.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_total_count(self) -> int:
        result = await self.session.execute(select(func.count(Document.id)))
        return result.scalar_one_or_none() or 0

    async def get_status_counts(self) -> dict:
        stmt = select(Document.status, func.count(Document.id)).group_by(Document.status)
        result = await self.session.execute(stmt)
        counts = {row[0]: row[1] for row in result.all()}
        total = sum(counts.values())
        return {
            "total": total,
            "processed": counts.get("Processed", 0),
            "pending": counts.get("Pending", 0),
            "failed": counts.get("Failed", 0)
        }

    async def get_collection_counts(self) -> List[dict]:
        stmt = select(Document.collection_id, func.count(Document.id)).group_by(Document.collection_id)
        result = await self.session.execute(stmt)
        return [{"collection_id": row[0] or "unassigned", "count": row[1]} for row in result.all()]

    async def get_letter_counts(self, collection_id: str) -> List[dict]:
        stmt = (
            select(func.upper(func.substr(Document.title, 1, 1)).label("letter"), func.count(Document.id))
            .where(Document.collection_id == collection_id)
            .group_by("letter")
            .order_by("letter")
        )
        result = await self.session.execute(stmt)
        return [{"letter": row[0], "count": row[1]} for row in result.all() if row[0] and row[0].isalpha()]

    async def delete(self, document_id: UUID) -> bool:
        document = await self.get_by_id(document_id)
        if document:
            await self.session.delete(document)
            await self.session.commit()
            return True
        return False

    async def get_total_chunks_count(self) -> int:
        result = await self.session.execute(select(func.count(DocumentChunk.id)))
        return result.scalar_one_or_none() or 0

    async def update_status(self, document_id: UUID, status: str) -> Optional[Document]:
        document = await self.get_by_id(document_id)
        if document:
            document.status = status
            await self.session.commit()
            await self.session.refresh(document)
        return document

    async def get_chunks_by_document_id(self, document_id: UUID) -> List[DocumentChunk]:
        stmt = select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_chunks_by_document_id(self, document_id: UUID) -> None:
        stmt = delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        await self.session.execute(stmt)
        await self.session.commit()

    async def save_chunks(self, chunks: List[DocumentChunk]) -> None:
        self.session.add_all(chunks)
        await self.session.commit()

    async def search_similar_chunks(self, query_embedding: list[float], limit: int = 5, threshold: float = 0.7) -> List[DocumentChunk]:
        """
        Uses pgvector's cosine_distance mapper to return the closest chunks.
        Returns the top-K closest chunks with their similarity scores attached.
        The threshold is applied by the calling service for context selection,
        but all top-K results are returned for monitoring/logging purposes.
        """
        distance_col = DocumentChunk.embedding.cosine_distance(query_embedding).label("distance")
        stmt = (
            select(DocumentChunk, distance_col)
            .where(DocumentChunk.embedding.isnot(None))
            .order_by(distance_col)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        
        chunks = []
        for chunk, distance in result.all():
            chunk.similarity = 1.0 - distance
            chunks.append(chunk)
        return chunks

    async def get_knowledge_metrics(self) -> List[dict]:
        """Fetch aggregated knowledge monitoring metrics for documents."""
        stmt = (
            select(
                Document.id.label("document_id"),
                Document.title.label("document_title"),
                Document.collection_id.label("collection_id"),
                func.count(DocumentChunk.id).label("chunk_count"),
                func.max(DocumentChunk.embedding_model).label("embedding_model"),
                Document.status
            )
            .outerjoin(DocumentChunk, Document.id == DocumentChunk.document_id)
            .group_by(Document.id, Document.status)
        )
        result = await self.session.execute(stmt)
        
        records = []
        for row in result:
            # Map database status to frontend expected status: "Active" | "Failed"
            # If a document is Processed or has chunks, it's Active.
            # If it's Failed, it's Failed.
            # If it's Pending, it might not have an embedding yet, we'll mark as Failed or Active.
            # To match the frontend semantics perfectly, we check if it's explicitly Failed.
            status = "Failed" if row.status == "Failed" else "Active"
            
            records.append({
                "documentId": str(row.document_id),
                "documentTitle": (row.document_title or "").strip() if getattr(row, "document_title", None) is not None else "",
                "collectionId": (row.collection_id or "unassigned").strip() if getattr(row, "collection_id", None) is not None else "unassigned",
                "chunkCount": row.chunk_count,
                "embeddingModel": row.embedding_model or "N/A",
                "status": status
            })
        return records
