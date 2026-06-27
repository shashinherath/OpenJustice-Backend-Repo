from typing import List
from uuid import UUID

from fastapi import UploadFile

from app.application.dtos.document_dto import DocumentCreateDto, DocumentResultDto
from app.application.exceptions.app_errors import AppError
from app.config import settings
from app.domain.interfaces.document_repository import IDocumentRepository
from app.domain.interfaces.storage_handler import IStorageHandler
from app.infrastructure.models.document import Document


class DocumentService:
    """Business logic for handling legal documents."""

    def __init__(self, repository: IDocumentRepository, storage: IStorageHandler):
        self.repository = repository
        self.storage = storage

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

    async def ingest_document(
        self, file: UploadFile, dto: DocumentCreateDto
    ) -> DocumentResultDto:
        """Validate, store physically, and record document metadata."""
        # 1. Validation
        if not file.filename:
            raise AppError("Missing filename", status_code=400, error_code="MISSING_FILENAME")
            
        ext = file.filename.split('.')[-1].lower()
        if ext not in settings.ALLOWED_DOCUMENT_FORMATS:
            raise AppError(f"Unsupported file format: {ext}. Allowed: {settings.ALLOWED_DOCUMENT_FORMATS}", status_code=400, error_code="UNSUPPORTED_FORMAT")

        # Optional: In a highly robust environment, we'd check byte size, 
        # but FastAPI limits can also be handled natively via middlewares.

        # 2. Extract bytes
        file_bytes = await file.read()
        
        if len(file_bytes) > settings.MAX_UPLOAD_SIZE:
            raise AppError(f"File size exceeds limit of {settings.MAX_UPLOAD_SIZE} bytes", status_code=413, error_code="FILE_TOO_LARGE")

        # 3. Store the file physically
        storage_path = await self.storage.upload_file(
            file_stream=file_bytes,
            file_name=file.filename,
            content_type=file.content_type or "application/octet-stream"
        )

        # 4. Save metadata to DB
        doc_model = Document(
            title=dto.title or file.filename,
            document_type=dto.document_type,
            language=dto.language or "en",
            storage_path=storage_path,
            published_year=dto.published_year,
            collection_id=dto.collection_id
        )

        doc_saved = await self.repository.create(doc_model)

        return self._map_to_dto(doc_saved)

    async def list_documents(
        self,
        skip: int = 0,
        limit: int = 25,
        search_query: str | None = None,
        language: str | None = None,
        status: str | None = None
    ) -> List[DocumentResultDto]:
        """Fetch all documents."""
        docs = await self.repository.list_documents(skip, limit, search_query, language, status)
        return [self._map_to_dto(d) for d in docs]

    async def get_document(self, document_id: UUID) -> DocumentResultDto:
        """Fetch a specific document."""
        doc = await self.repository.get_by_id(document_id)
        if not doc:
            raise AppError("Document not found", status_code=404, error_code="NOT_FOUND")
        return self._map_to_dto(doc)

    async def get_document_stats(self) -> dict:
        """Fetch document statistics by status."""
        return await self.repository.get_status_counts()

    async def delete_document(self, document_id: UUID) -> bool:
        """Delete document from database and storage."""
        doc = await self.repository.get_by_id(document_id)
        if not doc:
            raise AppError("Document not found", status_code=404, error_code="NOT_FOUND")
        
        # Delete from disk
        if doc.storage_path:
            await self.storage.delete_file(doc.storage_path)

        # Delete from DB
        return await self.repository.delete(document_id)
