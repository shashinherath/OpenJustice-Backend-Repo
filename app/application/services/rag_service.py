import os
import logging
from uuid import UUID

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_openai import OpenAIEmbeddings

from app.config import settings
from app.domain.interfaces.document_repository import IDocumentRepository
from app.infrastructure.models.document_chunk import DocumentChunk
from app.infrastructure.repositories.system_settings_repository import SystemSettingsRepository

logger = logging.getLogger(__name__)

class RAGService:
    """Orchestrates LangChain text splitting and OpenAI Vector Embedding."""

    def __init__(self, repository: IDocumentRepository, system_settings_repository: SystemSettingsRepository = None):
        self.repository = repository
        self.system_settings_repository = system_settings_repository
        
        # We still initialize a default embedding model here, but it will be overridden 
        # inside process_and_store_document() if dynamic settings are fetched.
        self.embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL, 
            api_key=settings.OPENAI_API_KEY
        )
        # We will use the LegalDocumentChunker logic internally inside process_and_store_document


    async def process_and_store_document(self, document_id: UUID, storage_path: str, language: str = "English"):
        """Extracts text depending on extension, chunks it, embeds it, and stores pgvector rows."""
        
        # Fetch dynamic settings
        chunk_size = settings.CHUNK_SIZE
        chunk_overlap = settings.CHUNK_OVERLAP
        embedding_model = settings.OPENAI_EMBEDDING_MODEL
        api_key = settings.OPENAI_API_KEY
        
        if self.system_settings_repository:
            sys_settings = await self.system_settings_repository.get_settings()
            chunk_size = sys_settings.retrieval_chunk_size
            chunk_overlap = sys_settings.retrieval_chunk_overlap
            embedding_model = sys_settings.retrieval_embedding_model
            if sys_settings.openai_api_key:
                api_key = sys_settings.openai_api_key
            
        # Re-initialize embeddings if model or key changed
        if embedding_model != self.embeddings.model or api_key != getattr(self.embeddings, 'api_key', settings.OPENAI_API_KEY):
            self.embeddings = OpenAIEmbeddings(
                model=embedding_model,
                api_key=api_key
            )
            
        logger.info(f"RAG settings: Chunk Size: {chunk_size}, Overlap: {chunk_overlap}, Model: {embedding_model}")

        # 1. Select the loader based on extension
        ext = storage_path.split('.')[-1].lower()
        if ext == 'pdf':
            loader = PyPDFLoader(storage_path)
        elif ext == 'txt':
            loader = TextLoader(storage_path, encoding="utf-8")
        else:
            logger.error(f"Unsupported extraction format for Document {document_id}")
            return
        
        
        try:
            # 2. Extract Document (usually synchronous IO)
            docs = loader.load()
            
            # 3. Split into manageable chunks using Legal Hierarchy
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            
            LEGAL_SEPARATORS = [
                "\n\n## ",  # Section headers
                "\n\n### ",  # Subsection headers
                "\n\n",  # Paragraphs
                "\n",  # Lines
                ". ",  # Sentences
                " "  # Words
            ]
            
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=LEGAL_SEPARATORS
            )
            
            splits = text_splitter.split_documents(docs)
            
            if not splits:
                logger.warning(f"No textual content extracted from Document {document_id}")
                return

            texts = [s.page_content for s in splits]
            
            # 4. Generate Embeddings (this hits the network)
            vectors = await self.embeddings.aembed_documents(texts)
            
            # 5. Assemble to Database Models
            db_chunks = []
            chunk_total = len(splits)
            
            for idx, (split, vector) in enumerate(zip(splits, vectors)):
                chunk = DocumentChunk(
                    document_id=document_id,
                    content=split.page_content,
                    language=language,
                    embedding=vector,
                    chunk_index=idx,
                    chunk_total=chunk_total,
                    chunk_size=len(split.page_content),
                    embedding_model=embedding_model,
                    embedding_version="v3",
                    chunking_version="v1"  # Version tracked!
                )
                chunk.metadata_ = split.metadata
                db_chunks.append(chunk)

            # 6. Push to repository saving vectors natively to pgvector
            await self.repository.save_chunks(db_chunks)
            await self.repository.update_status(document_id, "Processed")
            
            logger.info(f"Successfully vectorized and stored {chunk_total} chunks for Document {document_id}.")

        except Exception as e:
            await self.repository.update_status(document_id, "Failed")
            logger.error(f"Failed to process and embed document {document_id}: {str(e)}", exc_info=True)

