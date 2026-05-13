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
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
