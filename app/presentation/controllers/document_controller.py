from typing import List, Optional
from uuid import UUID
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.exceptions.app_errors import AppError
from app.application.services.rag_service import RAGService

from app.application.dtos.document_dto import DocumentCreateDto
from app.application.services.document_service import DocumentService
from app.config import settings
from app.infrastructure.db.base import get_db
from app.infrastructure.repositories.document_repository import DocumentRepository
from app.infrastructure.storage.local_storage import LocalStorageHandler
from app.presentation.schemas.document_schema import DocumentResponse, DocumentChunkResponse
from app.presentation.schemas.response_schema import SuccessResponse


router = APIRouter(prefix="/documents", tags=["Documents"])


def _get_storage_handler():
    """Return AzureBlobStorageHandler when Azure is configured, else LocalStorageHandler."""
    if settings.AZURE_STORAGE_CONNECTION_STRING or settings.AZURE_STORAGE_ACCOUNT_NAME:
        from app.infrastructure.storage.azure_blob_storage import AzureBlobStorageHandler
        return AzureBlobStorageHandler()
    return LocalStorageHandler(upload_dir="uploads")


def get_document_service(db: AsyncSession = Depends(get_db)) -> DocumentService:
    repository = DocumentRepository(db)
    storage = _get_storage_handler()
    return DocumentService(repository=repository, storage=storage)



def get_rag_service(db: AsyncSession = Depends(get_db)) -> RAGService:
    from app.infrastructure.repositories.system_settings_repository import SystemSettingsRepository
    from app.infrastructure.repositories.pg_llm_log_repository import PgLLMLogRepository
    repository = DocumentRepository(db)
    storage = _get_storage_handler()
    return RAGService(
        repository=repository, 
        system_settings_repository=SystemSettingsRepository(db),
        llm_log_repository=PgLLMLogRepository(db),
        storage_handler=storage
    )

@router.post(
    "/{document_id}/process",
    response_model=SuccessResponse[dict],
    status_code=status.HTTP_202_ACCEPTED
)
async def process_document(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    doc_service: DocumentService = Depends(get_document_service),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Manually trigger LangChain chunking and OpenAI pgvector embedding loop.
    Runs asynchronously in the background.
    """
    doc = await doc_service.get_document(document_id)
    if not doc.storage_path:
        raise AppError("Document has no physical storage path", status_code=400, error_code="NO_STORAGE_PATH")
        
    background_tasks.add_task(
        rag_service.process_and_store_document,
        document_id=document_id,
        storage_path=doc.storage_path,
        language=doc.language or "English"
    )
    
    return SuccessResponse(data={"job_status": "queued"}, message="Document is queued for LangChain decomposition and OpenAI pgvector embedding.")


@router.post(
    "",
    response_model=SuccessResponse[DocumentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    document_type: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
    published_year: Optional[int] = Form(None),
    collection_id: Optional[str] = Form(None),
    service: DocumentService = Depends(get_document_service),
):
    """
    Upload a legal document (PDF, TXT, DOCX) to the system.
    Note: Requires authentication/admin token based on environment setup.
    """
    # Ensure they're authenticated (mocking this conceptually based on get_current_user_id)
    # user = getattr(request.state, "user", None)
    
    dto = DocumentCreateDto(
        title=title,
        document_type=document_type,
        language=language,
        published_year=published_year,
        collection_id=collection_id,
    )
    
    result = await service.ingest_document(file=file, dto=dto)
    
    response_data = DocumentResponse.model_validate(result)
    
    return SuccessResponse(data=response_data, message="Document uploaded successfully")


@router.get(
    "",
    response_model=SuccessResponse[List[DocumentResponse]],
)
async def list_documents(
    skip: int = 0,
    limit: int = 25,
    search_query: Optional[str] = None,
    language: Optional[str] = None,
    status: Optional[str] = None,
    collection_id: Optional[str] = None,
    service: DocumentService = Depends(get_document_service),
):
    """Retrieve all ingested documents."""
    results = await service.list_documents(skip, limit, search_query, language, status, collection_id)
    response_data = [DocumentResponse.model_validate(r) for r in results]
    
    return SuccessResponse(data=response_data, message="Documents retrieved successfully")


@router.get(
    "/stats",
    response_model=SuccessResponse[dict],
)
async def get_document_stats(
    service: DocumentService = Depends(get_document_service),
):
    """Retrieve document statistics by status."""
    stats = await service.get_document_stats()
    return SuccessResponse(data=stats, message="Stats retrieved successfully")


@router.get(
    "/{document_id}",
    response_model=SuccessResponse[DocumentResponse],
)
async def get_document(
    document_id: UUID, 
    service: DocumentService = Depends(get_document_service)
):
    """Retrieve a specific document's metadata."""
    result = await service.get_document(document_id)
    response_data = DocumentResponse.model_validate(result)
    
    return SuccessResponse(data=response_data, message="Document retrieved successfully")


from fastapi.responses import RedirectResponse, FileResponse
import os

@router.get("/{document_id}/access")
async def get_document_access(
    document_id: UUID, 
    service: DocumentService = Depends(get_document_service)
):
    """Get a secure URL to access the document (e.g., SAS token for Azure)."""
    doc = await service.get_document(document_id)
    if not doc.storage_path:
        raise AppError("Document has no physical storage path", status_code=400, error_code="NO_STORAGE_PATH")

    storage_handler = _get_storage_handler()
    
    if hasattr(storage_handler, 'generate_sas_url') and "azure_blob_storage" in str(type(storage_handler)):
        # Generate SAS URL with same expiry as JWT token
        sas_url = await storage_handler.generate_sas_url(doc.storage_path, expiry_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return RedirectResponse(url=sas_url, status_code=302)
    elif "local_storage" in str(type(storage_handler)):
        if os.path.exists(doc.storage_path):
            return FileResponse(path=doc.storage_path, filename=os.path.basename(doc.storage_path))
        
        # Fallback if doc.storage_path is just a filename
        upload_dir = Path("uploads")
        if (upload_dir / doc.storage_path).exists():
            return FileResponse(path=str(upload_dir / doc.storage_path), filename=doc.storage_path)

    # Fallback to direct redirect (though if it's private, this will 404)
    return RedirectResponse(url=doc.storage_path, status_code=302)



@router.get(
    "/{document_id}/chunks",
    response_model=SuccessResponse[List[DocumentChunkResponse]],
)
async def get_document_chunks(
    document_id: UUID,
    service: DocumentService = Depends(get_document_service)
):
    """Retrieve all chunks for a specific document."""
    chunks = await service.get_document_chunks(document_id)
    response_data = [DocumentChunkResponse.model_validate(c) for c in chunks]
    return SuccessResponse(data=response_data, message="Chunks retrieved successfully")


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_document(
    document_id: UUID, 
    service: DocumentService = Depends(get_document_service)
):
    """Remove a document physically and from the database."""
    await service.delete_document(document_id)
    return SuccessResponse(data=None, message="Document deleted successfully")
