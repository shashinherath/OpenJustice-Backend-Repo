from typing import List, Optional
from uuid import UUID

from app.domain.interfaces.document_repository import IDocumentRepository
from app.application.dtos.document_dto import DocumentResultDto
from app.infrastructure.models.document import Document
from app.presentation.schemas.library_schema import (
    LibraryCollectionsResponse,
    LibraryLettersResponse,
    CollectionCount,
    LetterCount,
)

class LibraryService:
    """Service for public-facing library operations."""

    def __init__(self, repository: IDocumentRepository):
        self.repository = repository

    def _map_to_dto(self, doc: Document) -> DocumentResultDto:
        return DocumentResultDto(
            id=doc.id,
            title=doc.title,
            document_type=doc.document_type,
            language=doc.language,
            source_url=doc.source_url,
            storage_path=doc.storage_path,
            status=doc.status,
            published_year=doc.published_year,
            collection_id=doc.collection_id,
            created_at=doc.created_at,
        )

    async def get_collections_overview(self) -> LibraryCollectionsResponse:
        counts = await self.repository.get_collection_counts()
        collection_counts = [
            CollectionCount(collection_id=item["collection_id"], count=item["count"])
            for item in counts
        ]
        return LibraryCollectionsResponse(collections=collection_counts)

    async def get_letters_overview(self, collection_id: str) -> LibraryLettersResponse:
        counts = await self.repository.get_letter_counts(collection_id)
        letter_counts = [
            LetterCount(letter=item["letter"], count=item["count"])
            for item in counts
        ]
        return LibraryLettersResponse(collection_id=collection_id, letters=letter_counts)

    async def list_library_documents(
        self,
        collection_id: Optional[str] = None,
        letter: Optional[str] = None,
        search_query: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[DocumentResultDto]:
        # Fetch only processed/active documents for the public library view
        # We assume the library only shows processed documents for search and viewing
        docs = await self.repository.list_documents(
            skip=skip,
            limit=limit,
            search_query=search_query,
            status="Processed",
            collection_id=collection_id,
            letter=letter
        )
        return [self._map_to_dto(d) for d in docs]
