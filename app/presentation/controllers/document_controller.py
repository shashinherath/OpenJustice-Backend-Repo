from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.document_dto import DocumentCreateDto
from app.application.services.document_service import DocumentService
from app.infrastructure.db.base import get_db
from app.infrastructure.repositories.document_repository import DocumentRepository
from app.infrastructure.storage.local_storage import LocalStorageHandler
from app.presentation.schemas.document_schema import DocumentResponse
from app.presentation.schemas.response_schema import SuccessResponse


router = APIRouter(prefix="/documents", tags=["Documents"])


def get_document_service(db: AsyncSession = Depends(get_db)) -> DocumentService:
    repository = DocumentRepository(db)
    storage = LocalStorageHandler(upload_dir="uploads")
    return DocumentService(repository=repository, storage=storage)


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
    limit: int = 100,
    service: DocumentService = Depends(get_document_service),
):
    """Retrieve all ingested documents."""
    results = await service.list_documents(skip, limit)
    response_data = [DocumentResponse.model_validate(r) for r in results]
    
    return SuccessResponse(data=response_data, message="Documents retrieved successfully")


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
