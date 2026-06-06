import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.application.services.ai_evaluation_pipeline_service import background_evaluation_worker

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: spawn background task
    task = asyncio.create_task(background_evaluation_worker(interval_seconds=600))
    yield
    # Shutdown
    task.cancel()
