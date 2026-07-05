import io
from uuid import UUID
from fastapi import UploadFile

import pypdf
import docx

from app.application.exceptions.app_errors import AppError
from app.application.dtos.chat_dto import ConversationCreateDto
from app.application.services.chat_service import ChatService
from app.application.services.retrieval_service import RetrievalService
from app.application.services.llm_service import LLMService
from app.application.prompts.analyzer_prompts import AnalyzerPrompts

class DocumentAnalyzerService:
    """Service to analyze uploaded documents against the legal knowledge base."""

    def __init__(
        self,
        chat_service: ChatService,
        retrieval_service: RetrievalService,
        llm_service: LLMService,
    ):
        self.chat_service = chat_service
        self.retrieval_service = retrieval_service
        self.llm_service = llm_service

    async def analyze_document(
        self, user_id: UUID, file: UploadFile, document_type: str, analysis_type: str = "Risk & Compliance", custom_prompt: str = None
    ) -> dict:
        """Extracts text, retrieves legal context, runs analysis via LLM, and creates a conversation."""
        
        # 1. Extract text
        file_bytes = await file.read()
        filename = file.filename or "uploaded_document"
        ext = filename.split(".")[-1].lower()
        
        extracted_text = ""
        
        if ext == "pdf":
            try:
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text += text + "\n"
            except Exception as e:
                raise AppError(f"Failed to parse PDF: {str(e)}", status_code=400, error_code="PARSE_ERROR")
        elif ext in ["docx", "doc"]:
            try:
                doc = docx.Document(io.BytesIO(file_bytes))
                for para in doc.paragraphs:
                    extracted_text += para.text + "\n"
            except Exception as e:
                raise AppError(f"Failed to parse DOCX: {str(e)}", status_code=400, error_code="PARSE_ERROR")
        else:
            raise AppError(f"Unsupported file format: {ext}. Allowed: pdf, docx", status_code=400, error_code="UNSUPPORTED_FORMAT")

        if not extracted_text.strip():
            raise AppError("No text could be extracted from the document.", status_code=400, error_code="EMPTY_DOCUMENT")

        # 2. Get specific instructions
        analysis_instruction = AnalyzerPrompts.get_prompt(document_type, analysis_type, custom_prompt)

        # 3. Retrieve context from knowledge base
        # Use the first 1000 characters as a query representation of the document
        query_text = extracted_text[:1000].replace('\n', ' ')
        chunks, _ = await self.retrieval_service.retrieve(
            query=f"{document_type} context: {query_text}", 
            threshold=0.6
        )
        
        retrieved_context = "\n\n".join([c.content for c in chunks]) if chunks else "No specific related laws found in the knowledge base."

        # 4. Formulate the Context for the LLM
        llm_context = f"""
[ANALYSIS INSTRUCTIONS]
{analysis_instruction}

[LEGAL KNOWLEDGE BASE CONTEXT]
{retrieved_context}

[DOCUMENT CONTENT TO ANALYZE]
{extracted_text}
"""
        
        # 5. Create a new conversation
        conv_dto = ConversationCreateDto(
            title=f"Analysis: {filename}",
            channel="web"
        )
        conversation = await self.chat_service.create_conversation(user_id, conv_dto)

        import json
        user_query_data = {
            "intent": "document_analysis",
            "filename": filename,
            "file_extension": ext,
            "document_type": document_type,
            "analysis_type": analysis_type,
            "message": f"Hello! Please analyze the '{document_type}' document I have uploaded using the '{analysis_type}' analysis type. Please follow the analysis instructions carefully.",
            "document_text": extracted_text
        }
        user_query = json.dumps(user_query_data)
        
        # We don't stream here because we want the initial analysis to complete and return the conversation ID
        # so the frontend can redirect to the chat page where the analysis is already visible.
        await self.llm_service.generate_response(
            conversation_id=conversation.id,
            user_id=user_id,
            query=user_query,
            context=llm_context,
            message_type="text",
            save_ai_message=True
        )

        return {"conversation_id": str(conversation.id)}
