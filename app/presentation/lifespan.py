import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.application.services.ai_evaluation_pipeline_service import background_evaluation_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: spawn background evaluation worker
    task = asyncio.create_task(background_evaluation_worker(interval_seconds=600))
    yield
    # Shutdown: cancel the task and wait for it to actually stop.
    # Without awaiting, mid-DB operations could leave connections open on Azure
    # rolling restarts.
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
