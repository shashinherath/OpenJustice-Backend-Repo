import asyncio
import os
import re
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add the project root to the sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.infrastructure.db.base import async_session_maker
from app.infrastructure.models.document import Document

async def main():
    async with async_session_maker() as session:
        # Fetch all documents
        result = await session.execute(select(Document))
        documents = result.scalars().all()
        
        print(f"Found {len(documents)} documents to process.")
        
        for doc in documents:
            title = doc.title or ""
            
            # Extract document_type (extension)
            ext_match = re.search(r'\.(pdf|docx?)$', title, re.IGNORECASE)
            if ext_match:
                doc.document_type = ext_match.group(1).lower()
            else:
                if not doc.document_type:
                    doc.document_type = "pdf" # Default fallback
            
            # Extract published_year
            # E.g. "Act No. 9 of 2022" -> 2022
            # Or "1978Constitution" -> 1978
            year_match = re.search(r'\b(19|20)\d{2}\b', title)
            if year_match and not doc.published_year:
                doc.published_year = int(year_match.group(0))
                
            # Assign collection_id based on keywords
            title_lower = title.lower()
            if not doc.collection_id:
                if "act" in title_lower:
                    doc.collection_id = "acts"
                elif "slr" in title_lower:
                    doc.collection_id = "slr"
                elif "nlr" in title_lower:
                    doc.collection_id = "nlr"
                elif "sclr" in title_lower:
                    doc.collection_id = "sclr"
                elif "scoa" in title_lower:
                    doc.collection_id = "scoa"
                else:
                    doc.collection_id = "special"
                    
            print(f"Updated '{title}': type={doc.document_type}, year={doc.published_year}, collection={doc.collection_id}")
            
        await session.commit()
        print("Successfully backfilled document metadata.")

if __name__ == "__main__":
    asyncio.run(main())
