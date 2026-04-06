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
    async def list_documents(self, skip: int = 0, limit: int = 100) -> List[Document]:
        """Fetch all documents with pagination."""
        pass

    @abstractmethod
    async def delete(self, document_id: UUID) -> bool:
        """Delete a document by its ID."""
        pass

    @abstractmethod
    async def save_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Save vector chunks."""
        pass

    @abstractmethod
    async def search_similar_chunks(self, query_embedding: list[float], limit: int = 5) -> List[DocumentChunk]:
        """Retrieve the most semantically relevant chunks."""
        pass
