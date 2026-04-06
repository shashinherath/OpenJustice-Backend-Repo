import os
import uuid
import aiofiles
from pathlib import Path

from app.domain.interfaces.storage_handler import IStorageHandler

class LocalStorageHandler(IStorageHandler):
    """Saves files to the local disk."""

    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def upload_file(self, file_stream: bytes, file_name: str, content_type: str) -> str:
        unique_filename = f"{uuid.uuid4().hex}_{file_name}"
        file_path = self.upload_dir / unique_filename

        async with aiofiles.open(file_path, 'wb') as out_file:
            await out_file.write(file_stream)
            
        return str(file_path)

    async def delete_file(self, storage_path: str) -> bool:
        file_path = Path(storage_path)
        if file_path.exists():
            file_path.unlink()
            return True
        return False
