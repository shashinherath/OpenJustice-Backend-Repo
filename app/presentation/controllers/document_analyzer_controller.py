from uuid import UUID
from fastapi import APIRouter, Depends, Request, status, File, UploadFile, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.infrastructure.db.base import get_db
from app.application.services.chat_service import ChatService
from app.application.services.retrieval_service import RetrievalService
from app.application.services.llm_service import LLMService
from app.application.services.document_analyzer_service import DocumentAnalyzerService
from app.presentation.controllers.chat_controller import get_current_user_id, get_chat_service

from app.infrastructure.external.openai_client import OpenAIClient
from app.infrastructure.repositories.document_repository import DocumentRepository
from app.infrastructure.repositories.pgvector_semantic_cache_repository import PgVectorSemanticCacheRepository
from app.infrastructure.repositories.pg_llm_log_repository import PgLLMLogRepository
from app.infrastructure.repositories.pg_retrieval_log_repository import PgRetrievalLogRepository
from app.infrastructure.repositories.pg_citation_repository import PgCitationRepository
from app.infrastructure.repositories.system_settings_repository import SystemSettingsRepository

router = APIRouter(prefix="/analyzer", tags=["Analyzer"])

@router.post("/document", status_code=status.HTTP_201_CREATED)
async def analyze_document(
    request: Request,
    file: UploadFile = File(...),
    document_type: str = Form("General Document"),
    analysis_type: str = Form("Risk & Compliance"),
    custom_prompt: str = Form(None),
    db: AsyncSession = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service),
) -> Dict[str, Any]:
    """Upload a document to be analyzed and create a new chat conversation with the results."""
    
    user_id = get_current_user_id(request)
    
    # Initialize repositories
    doc_repo = DocumentRepository(db)
    retrieval_log_repo = PgRetrievalLogRepository(db)
    sys_settings_repo = SystemSettingsRepository(db)
    llm_log_repo = PgLLMLogRepository(db)
    semantic_cache = PgVectorSemanticCacheRepository(db)
    citation_repo = PgCitationRepository(db)
    
    # Initialize services
    retrieval_service = RetrievalService(
        doc_repo, 
        log_repository=retrieval_log_repo,
        system_settings_repository=sys_settings_repo,
        llm_log_repository=llm_log_repo
    )
    
    llm_service = LLMService(
        chat_service, 
        OpenAIClient(system_settings_repository=sys_settings_repo), 
        semantic_cache=semantic_cache, 
        llm_log_repository=llm_log_repo,
        citation_repository=citation_repo,
        system_settings_repository=sys_settings_repo
    )
    
    analyzer_service = DocumentAnalyzerService(
        chat_service=chat_service,
        retrieval_service=retrieval_service,
        llm_service=llm_service
    )
    
    result = await analyzer_service.analyze_document(
        user_id=user_id,
        file=file,
        document_type=document_type,
        analysis_type=analysis_type,
        custom_prompt=custom_prompt
    )
    
    return result
