import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from app.infrastructure.db.base import Base

class SemanticCache(Base):
    """
    Semantic cache mapping previously asked queries to generated responses.
    Uses pgvector for semantic search (e.g. 95% similarity match).
    """
    __tablename__ = "semantic_caches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_text = Column(String, nullable=False)
    # The embeddings are typically 1536 (text-embedding-3-small) or 3072 (text-embedding-3-large).
    # Since text-embedding-3-large is used by default in config, we allocate 3072.
    query_embedding = Column(Vector(3072), nullable=False)
    response_text = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
