import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

logger = logging.getLogger(__name__)

class VectorCleanupService:
    """Clean up orphaned and archived pgvector chunks."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_orphaned_chunks(self) -> List[str]:
        """Find chunks referencing deleted documents."""
        # Using string ID for postgres UUID
        sql = text("""
            SELECT dc.id
            FROM document_chunks dc
            LEFT JOIN documents d ON dc.document_id = d.id
            WHERE d.id IS NULL
        """)

        result = await self.db.execute(sql)
        orphaned_ids = [str(row.id) for row in result.fetchall()]

        if orphaned_ids:
            logger.info(f"Found {len(orphaned_ids)} orphaned chunks")
        return orphaned_ids

    async def find_archived_chunks(self, older_than_days: int = 30) -> List[str]:
        """Find archived chunks older than threshold."""
        sql = text("""
            SELECT id
            FROM document_chunks
            WHERE metadata->>'archived' = 'true'
            AND (metadata->>'archived_at')::timestamp < NOW() - :days * INTERVAL '1 day'
        """)

        result = await self.db.execute(sql, {"days": older_than_days})
        archived_ids = [str(row.id) for row in result.fetchall()]

        if archived_ids:
            logger.info(f"Found {len(archived_ids)} archived chunks older than {older_than_days} days")
        return archived_ids

    async def delete_chunks_batch(self, chunk_ids: List[str], batch_size: int = 100):
        """Delete chunks in batches safely."""
        total = len(chunk_ids)
        for i in range(0, total, batch_size):
            batch = chunk_ids[i:i+batch_size]

            sql = text("DELETE FROM document_chunks WHERE id::text = ANY(:ids)")
            await self.db.execute(sql, {"ids": batch})
            await self.db.commit()

            logger.info(f"Deleted batch {i//batch_size + 1}: {len(batch)} chunks")

    async def cleanup_old_vectors(self):
        """Execute full cleanup process."""
        orphaned = await self.find_orphaned_chunks()
        archived = await self.find_archived_chunks(older_than_days=30)

        # Combine and deduplicate
        to_delete = list(set(orphaned + archived))

        if to_delete:
            logger.warning(f"Deleting {len(to_delete)} obsolete pgvector chunks...")
            await self.delete_chunks_batch(to_delete)
        else:
            logger.info("No obsolete vector chunks to delete")
