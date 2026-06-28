from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.library_service import LibraryService
from app.infrastructure.db.base import get_db
from app.infrastructure.repositories.document_repository import DocumentRepository
from app.presentation.schemas.response_schema import SuccessResponse
from app.presentation.schemas.document_schema import DocumentResponse
from app.presentation.schemas.library_schema import (
    LibraryCollectionsResponse,
    LibraryLettersResponse,
)

router = APIRouter(prefix="/library", tags=["library"])

def get_library_service(db: AsyncSession = Depends(get_db)) -> LibraryService:
    repository = DocumentRepository(db)
    return LibraryService(repository)

@router.get(
    "/collections",
    response_model=SuccessResponse[LibraryCollectionsResponse],
    status_code=status.HTTP_200_OK,
)
async def get_collections(
    service: LibraryService = Depends(get_library_service),
):
    """Get document counts grouped by collection."""
    result = await service.get_collections_overview()
    return SuccessResponse(data=result, message="Collections fetched successfully")

@router.get(
    "/collections/{collection_id}/letters",
    response_model=SuccessResponse[LibraryLettersResponse],
    status_code=status.HTTP_200_OK,
)
async def get_letters(
    collection_id: str,
    service: LibraryService = Depends(get_library_service),
):
    """Get document counts grouped by starting letter for a specific collection."""
    result = await service.get_letters_overview(collection_id)
    return SuccessResponse(data=result, message="Letters fetched successfully")

@router.get(
    "/documents",
    response_model=SuccessResponse[List[DocumentResponse]],
    status_code=status.HTTP_200_OK,
)
async def list_library_documents(
    collection_id: Optional[str] = Query(None, description="The collection ID to filter by"),
    letter: Optional[str] = Query(None, description="The starting letter to filter by"),
    search_query: Optional[str] = Query(None, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: LibraryService = Depends(get_library_service),
):
    """List documents for the library view."""
    results = await service.list_library_documents(
        collection_id=collection_id,
        letter=letter,
        search_query=search_query,
        skip=skip,
        limit=limit,
    )
    
    response_data = [DocumentResponse.model_validate(r) for r in results]
    return SuccessResponse(data=response_data, message="Library documents fetched successfully")
