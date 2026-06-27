"""Main API router."""
from fastapi import APIRouter

from app.presentation.controllers.auth_controller import router as auth_router
from app.presentation.controllers.whatsapp_controller import router as whatsapp_router
from app.presentation.controllers.chat_controller import router as chat_router
from app.presentation.controllers.document_controller import router as document_router
from app.presentation.controllers.websocket_controller import router as websocket_router


from app.presentation.controllers.admin_controller import router as admin_router
from app.presentation.controllers.library_controller import router as library_router

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(whatsapp_router)
api_router.include_router(chat_router)
api_router.include_router(document_router)
api_router.include_router(websocket_router)
api_router.include_router(admin_router)
api_router.include_router(library_router)
