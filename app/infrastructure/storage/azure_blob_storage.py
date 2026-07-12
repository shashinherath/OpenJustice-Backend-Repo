"""Azure Blob Storage handler implementing IStorageHandler."""
import logging
import uuid
from pathlib import Path

from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.core.exceptions import ResourceNotFoundError

from app.config import settings
from app.domain.interfaces.storage_handler import IStorageHandler

logger = logging.getLogger(__name__)


class AzureBlobStorageHandler(IStorageHandler):
    """
    Stores files in Azure Blob Storage.

    Authentication priority:
      1. AZURE_STORAGE_CONNECTION_STRING (explicit connection string — recommended for dev/staging)
      2. AZURE_STORAGE_ACCOUNT_NAME + Managed Identity (recommended for production on Azure)
    """

    def __init__(self) -> None:
        self.container_name = settings.AZURE_STORAGE_CONTAINER_NAME

        if settings.AZURE_STORAGE_CONNECTION_STRING:
            self._client = BlobServiceClient.from_connection_string(
                settings.AZURE_STORAGE_CONNECTION_STRING
            )
            logger.info("AzureBlobStorageHandler: using connection string auth.")
        elif settings.AZURE_STORAGE_ACCOUNT_NAME:
            from azure.identity import ManagedIdentityCredential
            credential = ManagedIdentityCredential()
            account_url = f"https://{settings.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net"
            self._client = BlobServiceClient(account_url=account_url, credential=credential)
            logger.info("AzureBlobStorageHandler: using Managed Identity auth.")
        else:
            raise RuntimeError(
                "Azure Blob Storage is not configured. "
                "Set AZURE_STORAGE_CONNECTION_STRING or AZURE_STORAGE_ACCOUNT_NAME."
            )

        self._ensure_container()

    def _ensure_container(self) -> None:
        """Create the blob container if it doesn't already exist."""
        try:
            container_client = self._client.get_container_client(self.container_name)
            container_client.get_container_properties()
        except ResourceNotFoundError:
            self._client.create_container(self.container_name)
            logger.info(f"Created blob container: {self.container_name}")
        except Exception as exc:
            logger.warning(f"Could not verify blob container existence: {exc}")

    async def upload_file(
        self,
        file_stream: bytes,
        file_name: str,
        content_type: str,
        folder: str = "",
    ) -> str:
        """
        Upload bytes to Azure Blob Storage.

        Blobs are stored as "<folder>/<uuid><ext>" creating a virtual directory
        structure visible in the Azure Portal and Storage Explorer.

        Returns the public blob URL.
        """
        ext = Path(file_name).suffix or ""
        unique_name = f"{uuid.uuid4().hex}{ext}"
        blob_name = f"{folder.strip('/')}/{unique_name}" if folder else unique_name

        blob_client = self._client.get_blob_client(
            container=self.container_name,
            blob=blob_name,
        )

        blob_client.upload_blob(
            data=file_stream,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type),
        )

        blob_url = blob_client.url
        logger.info(f"Uploaded blob: {blob_url}")
        return blob_url

    async def delete_file(self, storage_path: str) -> bool:
        """
        Delete a blob given its full URL or blob name.

        Accepts either:
          - Full URL:  https://<account>.blob.core.windows.net/<container>/<blob>
          - Blob name: <uuid>.pdf
        """
        # Extract just the blob name from a full URL
        if storage_path.startswith("https://"):
            # URL format: https://<account>.blob.core.windows.net/<container>/<blob_name>
            blob_name = storage_path.split(f"/{self.container_name}/", 1)[-1]
        else:
            blob_name = storage_path

        try:
            blob_client = self._client.get_blob_client(
                container=self.container_name,
                blob=blob_name,
            )
            blob_client.delete_blob()
            logger.info(f"Deleted blob: {blob_name}")
            return True
        except ResourceNotFoundError:
            logger.warning(f"Blob not found for deletion: {blob_name}")
            return False
        except Exception as exc:
            logger.error(f"Failed to delete blob {blob_name}: {exc}")
            return False

    async def download_file(self, storage_path: str, destination_path: str) -> bool:
        """Download a blob given its full URL or blob name to a local path."""
        import aiofiles
        if storage_path.startswith("https://"):
            blob_name = storage_path.split(f"/{self.container_name}/", 1)[-1]
        else:
            blob_name = storage_path

        try:
            blob_client = self._client.get_blob_client(
                container=self.container_name,
                blob=blob_name,
            )
            download_stream = blob_client.download_blob()
            async with aiofiles.open(destination_path, 'wb') as dst:
                await dst.write(download_stream.readall())
            return True
        except ResourceNotFoundError:
            logger.warning(f"Blob not found for download: {blob_name}")
            return False
        except Exception as exc:
            logger.error(f"Failed to download blob {blob_name}: {exc}")
            return False
