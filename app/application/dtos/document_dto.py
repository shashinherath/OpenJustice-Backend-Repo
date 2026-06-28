import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class DocumentCreateDto:
    title: Optional[str] = None
    document_type: Optional[str] = None
    language: Optional[str] = None
    published_year: Optional[int] = None
    collection_id: Optional[str] = None


@dataclass(frozen=True)
class DocumentResultDto:
    id: uuid.UUID
    title: Optional[str]
    document_type: Optional[str]
    language: Optional[str]
    source_url: Optional[str]
    storage_path: Optional[str]
    status: str
    published_year: Optional[int]
    collection_id: Optional[str]
    created_at: datetime
