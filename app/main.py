"""FastAPI application entrypoint."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.presentation.middleware.auth_middleware import AuthMiddleware
from app.presentation.middleware.error_handler import setup_error_handlers
from app.presentation.routes.api import api_router
from app.presentation.lifespan import lifespan

# Disable interactive API docs in production to avoid exposing the schema publicly.
# In development (DEBUG=True) they remain available at /docs and /redoc.
_docs_url = "/docs" if settings.DEBUG else None
_redoc_url = "/redoc" if settings.DEBUG else None
_openapi_url = "/openapi.json" if settings.DEBUG else None

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Middlewares
app.add_middleware(AuthMiddleware)

# Register Error Handlers
setup_error_handlers(app)

app.include_router(api_router)


# ── Health check ──────────────────────────────────────────────
# Azure Container Apps / App Service uses this path as its liveness
# and readiness probe. The AuthMiddleware already whitelists /health.
@app.get("/health", include_in_schema=False, tags=["ops"])
async def health_check() -> JSONResponse:
    """Liveness/readiness probe for Azure health probes."""
    return JSONResponse(
        {"status": "ok", "version": settings.APP_VERSION},
        status_code=200,
    )


# ── Static file mounts ────────────────────────────────────────
# NOTE: In Azure these directories are on the ephemeral container
# filesystem. Files will be lost on restart. For persistence,
# migrate to Azure Blob Storage (see azure_deployment_analysis.md).
os.makedirs(settings.AUDIO_TEMP_DIR, exist_ok=True)
os.makedirs(settings.AUDIO_MEDIA_DIR, exist_ok=True)
os.makedirs("uploads", exist_ok=True)

app.mount("/media", StaticFiles(directory=settings.AUDIO_MEDIA_DIR), name="media")
app.mount("/temp", StaticFiles(directory=settings.AUDIO_TEMP_DIR), name="temp")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
