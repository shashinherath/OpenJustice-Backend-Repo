"""FastAPI application entrypoint."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.presentation.middleware.auth_middleware import AuthMiddleware
from app.presentation.middleware.error_handler import setup_error_handlers
from app.presentation.routes.api import api_router


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
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
