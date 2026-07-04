"""Global error handler middleware."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.application.exceptions import AppError
from app.domain.exceptions import AuthenticationFailure, UserAlreadyExistsError
from app.presentation.schemas.response_schema import ErrorDetail, ErrorResponse
import traceback
from app.application.services.system_error_logger import log_system_error


def setup_error_handlers(app: FastAPI) -> None:
    """Set up all global exception handlers for the FastAPI app."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        content = ErrorResponse(
            error=ErrorDetail(code=exc.error_code, message=exc.message)
        ).model_dump(mode="json")
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(UserAlreadyExistsError)
    async def user_already_exists_handler(
        request: Request, exc: UserAlreadyExistsError
    ) -> JSONResponse:
        content = ErrorResponse(
            error=ErrorDetail(code="USER_ALREADY_EXISTS", message=exc.message)
        ).model_dump(mode="json")
        return JSONResponse(status_code=409, content=content)

    @app.exception_handler(AuthenticationFailure)
    async def authentication_failure_handler(
        request: Request, exc: AuthenticationFailure
    ) -> JSONResponse:
        await log_system_error(
            error_type="AUTH",
            message=exc.message,
            details=f"Path: {request.url.path}\n{traceback.format_exc()}"
        )
        content = ErrorResponse(
            error=ErrorDetail(code="AUTHENTICATION_ERROR", message=exc.message)
        ).model_dump(mode="json")
        return JSONResponse(status_code=401, content=content)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        await log_system_error(
            error_type="SYSTEM",
            message=str(exc) or "Unhandled Server Exception",
            details=f"Path: {request.url.path}\n{traceback.format_exc()}"
        )
        content = ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred. Please try again.",
            )
        ).model_dump(mode="json")
        return JSONResponse(status_code=500, content=content)
