import os
import logging
from uuid import UUID

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_openai import OpenAIEmbeddings

from app.config import settings
from app.domain.interfaces.document_repository import IDocumentRepository
from app.infrastructure.models.document_chunk import DocumentChunk

logger = logging.getLogger(__name__)

class RAGService:
    """Orchestrates LangChain text splitting and OpenAI Vector Embedding."""

    def __init__(self, repository: IDocumentRepository):
        self.repository = repository
        self.embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL, 
            api_key=settings.OPENAI_API_KEY
        )
        # We will use the LegalDocumentChunker logic internally inside process_and_store_document


    async def process_and_store_document(self, document_id: UUID, storage_path: str, language: str = "English"):
        """Extracts text depending on extension, chunks it, embeds it, and stores pgvector rows."""
        
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
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
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
                    embedding_model=settings.OPENAI_EMBEDDING_MODEL,
                    embedding_version="v3",
                    chunking_version="v1"  # Version tracked!
                )
                chunk.metadata_ = split.metadata
                db_chunks.append(chunk)

            # 6. Push to repository saving vectors natively to pgvector
            await self.repository.save_chunks(db_chunks)
            
            logger.info(f"Successfully vectorized and stored {chunk_total} chunks for Document {document_id}.")

        except Exception as e:
            logger.error(f"Failed to process and embed document {document_id}: {str(e)}", exc_info=True)

