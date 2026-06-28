from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    """Schema for presenting document metadata."""

    id: UUID
    title: Optional[str]
    document_type: Optional[str]
    language: Optional[str]
    source_url: Optional[str]
    storage_path: Optional[str]
    status: str
    published_year: Optional[int]
    collection_id: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentChunkResponse(BaseModel):
    """Schema for presenting chunk details."""

    id: UUID
    document_id: UUID
    content: str
    language: str
    chunk_index: int
    chunk_total: int
    chunk_size: int
    embedding_model: Optional[str]
    metadata_: Optional[dict]

    model_config = ConfigDict(from_attributes=True)
