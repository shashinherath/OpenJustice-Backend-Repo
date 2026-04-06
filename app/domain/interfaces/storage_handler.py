import io
from abc import ABC, abstractmethod


class IStorageHandler(ABC):
    """Interface for document and media storage operations."""

    @abstractmethod
    async def upload_file(self, file_stream: bytes, file_name: str, content_type: str) -> str:
        """Upload a file and return its storage path or URL."""
        pass

    @abstractmethod
    async def delete_file(self, storage_path: str) -> bool:
        """Delete a file from storage."""
        pass
