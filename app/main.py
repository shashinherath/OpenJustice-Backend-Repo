"""FastAPI application entrypoint."""
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.presentation.middleware.auth_middleware import AuthMiddleware
from app.presentation.middleware.error_handler import setup_error_handlers
from app.presentation.routes.api import api_router

from app.presentation.lifespan import lifespan

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
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

# Serve persisted audio files so voice notes remain playable after refresh/login
os.makedirs(settings.AUDIO_TEMP_DIR, exist_ok=True)
os.makedirs(settings.AUDIO_MEDIA_DIR, exist_ok=True)
os.makedirs("uploads", exist_ok=True)

app.mount("/media", StaticFiles(directory=settings.AUDIO_MEDIA_DIR), name="media")
app.mount("/temp", StaticFiles(directory=settings.AUDIO_TEMP_DIR), name="temp")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
