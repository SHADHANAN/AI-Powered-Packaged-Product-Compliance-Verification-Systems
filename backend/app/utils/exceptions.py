from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.utils.logging import get_logger

logger = get_logger("app.exceptions")


class AppException(Exception):
    """Base application exception with consistent status code and structure."""

    def __init__(
        self,
        message: str = "An application error occurred",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details
        self.headers = headers


class NotFoundException(AppException):
    """Exception raised when a requested resource is not found."""

    def __init__(self, message: str = "Resource not found", details: Optional[Any] = None):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND, details=details)


class BadRequestException(AppException):
    """Exception raised for invalid client requests."""

    def __init__(self, message: str = "Bad request", details: Optional[Any] = None):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST, details=details)


class UnauthorizedException(AppException):
    """Exception raised for authentication failures."""

    def __init__(
        self,
        message: str = "Could not validate credentials",
        details: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
            headers=headers or {"WWW-Authenticate": "Bearer"},
        )


class PayloadTooLargeException(AppException):
    """Exception raised when uploaded payload or file exceeds maximum allowed size."""

    def __init__(self, message: str = "Payload too large", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            details=details,
        )


class InternalServerErrorException(AppException):
    """Exception raised for unrecoverable server errors."""

    def __init__(self, message: str = "Internal server error", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions."""
    logger.warning(f"AppException on {request.method} {request.url.path}: {exc.message}")
    content = {
        "success": False,
        "error": {
            "message": exc.message,
            "status_code": exc.status_code,
            "details": exc.details,
        },
    }
    return JSONResponse(status_code=exc.status_code, content=content, headers=exc.headers)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle standard Starlette / FastAPI HTTPExceptions."""
    logger.warning(f"HTTPException on {request.method} {request.url.path}: {exc.detail}")
    content = {
        "success": False,
        "error": {
            "message": str(exc.detail),
            "status_code": exc.status_code,
            "details": None,
        },
    }
    headers = getattr(exc, "headers", None)
    return JSONResponse(status_code=exc.status_code, content=content, headers=headers)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic request validation errors."""
    logger.warning(f"ValidationError on {request.method} {request.url.path}: {exc.errors()}")
    content = {
        "success": False,
        "error": {
            "message": "Invalid request parameters",
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "details": exc.errors(),
        },
    }
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=content)


async def integrity_exception_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """Handle database constraint violations without leaking raw SQL or schema internals."""
    logger.warning(f"IntegrityError on {request.method} {request.url.path}: {str(exc.orig) if hasattr(exc, 'orig') else str(exc)}")
    content = {
        "success": False,
        "error": {
            "message": "Database constraint violation. Check for duplicate or conflicting references.",
            "status_code": status.HTTP_400_BAD_REQUEST,
            "details": None,
        },
    }
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=content)


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle general database errors securely."""
    logger.error(f"SQLAlchemyError on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    content = {
        "success": False,
        "error": {
            "message": "A database operation error occurred. Please try again later.",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "details": None,
        },
    }
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=content)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unhandled exceptions to prevent exposing internals."""
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    content = {
        "success": False,
        "error": {
            "message": "An unexpected error occurred. Please try again later.",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "details": None,
        },
    }
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=content)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI application."""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
