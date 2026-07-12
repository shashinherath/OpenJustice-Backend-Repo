import io
from abc import ABC, abstractmethod


class IStorageHandler(ABC):
    """Interface for document and media storage operations."""

    @abstractmethod
    async def upload_file(
        self,
        file_stream: bytes,
        file_name: str,
        content_type: str,
        folder: str = "",
    ) -> str:
        """Upload a file and return its storage path or URL.

        Args:
            file_stream: Raw file bytes.
            file_name:   Original file name (used for extension only).
            content_type: MIME type of the file.
            folder:      Virtual folder/prefix, e.g. "documents" or "audio/media".
                         An empty string means the container root.
        """
        pass

    @abstractmethod
    async def delete_file(self, storage_path: str) -> bool:
        """Delete a file from storage."""
        pass

    @abstractmethod
    async def download_file(self, storage_path: str, destination_path: str) -> bool:
        """Download a file from storage to a local destination path."""
        pass
