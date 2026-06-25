from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.infrastructure.models.document import Document
from app.infrastructure.models.document_chunk import DocumentChunk


class IDocumentRepository(ABC):
    """Interface for document database operations."""

    @abstractmethod
    async def create(self, document: Document) -> Document:
        """Save a new document record."""
        pass

    @abstractmethod
    async def get_by_id(self, document_id: UUID) -> Optional[Document]:
        """Fetch a document by its ID."""
        pass

    @abstractmethod
    async def list_documents(
        self,
        skip: int = 0,
        limit: int = 25,
        search_query: Optional[str] = None,
        language: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Document]:
        """Fetch all documents with pagination and optional filters."""
        pass

    @abstractmethod
    async def delete(self, document_id: UUID) -> bool:
        """Delete a document by its ID."""
        pass

    @abstractmethod
    async def get_total_count(self) -> int:
        """Return the total number of documents."""
        pass

    @abstractmethod
    async def update_status(self, document_id: UUID, status: str) -> Optional[Document]:
        """Update the processing status of a document."""
        pass

    @abstractmethod
    async def save_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Save vector chunks."""
        pass

    @abstractmethod
    async def search_similar_chunks(self, query_embedding: list[float], limit: int = 5) -> List[DocumentChunk]:
        """Retrieve the most semantically relevant chunks."""
        pass

    @abstractmethod
    async def get_knowledge_metrics(self) -> List[dict]:
        """Fetch aggregated knowledge monitoring metrics for documents."""
        pass

    @abstractmethod
    async def get_total_chunks_count(self) -> int:
        """Return the total number of document chunks."""
        pass

    @abstractmethod
    async def get_status_counts(self) -> dict:
        """Fetch count of documents by status."""
        pass
