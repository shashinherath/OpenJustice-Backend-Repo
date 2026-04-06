from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.infrastructure.models.document import Document


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
