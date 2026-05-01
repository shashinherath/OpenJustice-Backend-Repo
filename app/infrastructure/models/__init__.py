"""
Infrastructure Models

SQLAlchemy ORM models for database persistence.
Import order matters — models with FK dependencies must be imported after
the tables they reference so Base.metadata is correctly populated.
"""

# Users & Auth
from app.infrastructure.models.user import User  # noqa: F401
from app.infrastructure.models.user_session import UserSession  # noqa: F401

# Conversation System
from app.infrastructure.models.conversation import Conversation  # noqa: F401
from app.infrastructure.models.message import Message  # noqa: F401

# Legal Documents
from app.infrastructure.models.document import Document  # noqa: F401
from app.infrastructure.models.document_chunk import DocumentChunk  # noqa: F401

# RAG Retrieval & Cache
from app.infrastructure.models.retrieval_log import RetrievalLog  # noqa: F401
from app.infrastructure.models.retrieved_document import RetrievedDocument  # noqa: F401
from app.infrastructure.models.semantic_cache import SemanticCache  # noqa: F401

# Citations
from app.infrastructure.models.citation import Citation  # noqa: F401

# LLM Traceability
from app.infrastructure.models.llm_request import LLMRequest  # noqa: F401
from app.infrastructure.models.llm_response import LLMResponse  # noqa: F401

# Multilingual Support
from app.infrastructure.models.translation import Translation  # noqa: F401

# Audio Processing
from app.infrastructure.models.audio_request import AudioRequest  # noqa: F401

# Audit
from app.infrastructure.models.audit_log import AuditLog  # noqa: F401
