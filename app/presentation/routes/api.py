"""Main API router."""
from fastapi import APIRouter

from app.presentation.controllers.auth_controller import router as auth_router
from app.presentation.controllers.whatsapp_controller import router as whatsapp_router


api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(whatsapp_router)
