"""Database initialization utilities."""
import asyncio
from sqlalchemy import text
from app.infrastructure.db.base import engine, Base
from app.infrastructure import models  # noqa: F401
from app.config import settings


async def init_db() -> None:
    """
    Initialize database:
    - Create all tables
    - Install pgvector extension
    - Run any necessary setup
    """
    async with engine.begin() as conn:
        # Install pgvector extension if not exists
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        
    print("Database initialized successfully")


async def drop_db() -> None:
    """
    Drop all tables (use with caution!).
    Only for development/testing purposes.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    print("WARNING: All tables dropped")


async def reset_db() -> None:
    """
    Reset database by dropping and recreating all tables.
    Only for development/testing purposes.
    """
    await drop_db()
    await init_db()
    print("Database reset complete")


async def check_db_connection() -> bool:
    """
    Check if database connection is working.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print("Database connection successful")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


if __name__ == "__main__":
    # Run initialization when script is executed directly
    asyncio.run(init_db())
