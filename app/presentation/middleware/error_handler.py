"""Global error handler middleware."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.application.exceptions import AppError
from app.domain.exceptions import AuthenticationFailure
from app.presentation.schemas.response_schema import ErrorDetail, ErrorResponse


def setup_error_handlers(app: FastAPI) -> None:
    """Set up all global exception handlers for the FastAPI app."""

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
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        content = ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred. Please try again.",
            )
        ).model_dump()
        return JSONResponse(status_code=500, content=content)
