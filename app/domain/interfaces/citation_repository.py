from abc import ABC, abstractmethod
import uuid
from typing import List

class ICitationRepository(ABC):
    """Interface for enforcing AI hallucinations bounds via citations."""

    @abstractmethod
    async def log_citations(
        self,
        message_id: uuid.UUID,
        document_ids: List[uuid.UUID]
    ) -> None:
        """Links the generated text message to the specific source documents cited."""
        pass
