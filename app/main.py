"""FastAPI application entrypoint."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.application.exceptions import AppError
from app.config import settings
from app.domain.exceptions import AuthenticationFailure
from app.presentation.routes.api import api_router
from app.presentation.schemas.response_schema import ErrorDetail, ErrorResponse


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

app.include_router(api_router)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    content = ErrorResponse(
        error=ErrorDetail(code=exc.error_code, message=exc.message)
    ).model_dump()
    return JSONResponse(status_code=exc.status_code, content=content)


@app.exception_handler(AuthenticationFailure)
async def authentication_failure_handler(
    request: Request, exc: AuthenticationFailure
) -> JSONResponse:
    content = ErrorResponse(
        error=ErrorDetail(code="AUTHENTICATION_ERROR", message=exc.message)
    ).model_dump()
    return JSONResponse(status_code=401, content=content)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    content = ErrorResponse(
        error=ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred. Please try again.",
        )
    ).model_dump()
    return JSONResponse(status_code=500, content=content)
