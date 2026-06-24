"""Global exception handlers and unified API response helpers."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.common import ApiResponse


def make_error_response(message: str, status_code: int = 400) -> JSONResponse:
    """Build a JSONResponse using the unified error wrapper."""
    body = ApiResponse(
        success=False,
        message=message,
        data=None,
        error=message,
    )
    return JSONResponse(status_code=status_code, content=body.model_dump())


def add_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI application."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return make_error_response(
            message=exc.detail or "Request error",
            status_code=exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ):
        detail = exc.errors()
        message = detail[0]["msg"] if detail else "Validation error"
        return make_error_response(message=message, status_code=422)

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(
        request: Request,
        exc: ValidationError,
    ):
        return make_error_response(
            message=str(exc.errors()[0]["msg"]),
            status_code=422,
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        return make_error_response(
            message="Database error",
            status_code=500,
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return make_error_response(
            message="Internal server error",
            status_code=500,
        )
