from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.config import get_settings
from app.schemas.common import RootResponse
from app.utils.exceptions import register_exception_handlers
from app.utils.logging import get_logger, setup_logging

settings = get_settings()
logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle events."""
    setup_logging(log_level=settings.LOG_LEVEL)
    logger.info(
        f"Starting {settings.APP_NAME} v{settings.APP_VERSION} "
        f"[env={settings.ENVIRONMENT}, debug={settings.DEBUG}]"
    )
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


def create_application() -> FastAPI:
    """Application factory for the FastAPI backend service."""
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register global exception handlers
    register_exception_handlers(app)

    # Mount API routers
    app.include_router(api_router, prefix=settings.API_PREFIX)

    # Root endpoint
    @app.get(
        "/",
        response_model=RootResponse,
        status_code=status.HTTP_200_OK,
        tags=["Root"],
        summary="Service Root",
        description="Verify service availability and discover API documentation links.",
    )
    async def root() -> RootResponse:
        return RootResponse(
            message=f"{settings.APP_NAME} is running",
            app_name=settings.APP_NAME,
            version=settings.APP_VERSION,
            environment=settings.ENVIRONMENT,
            docs_url="/docs",
        )

    return app


app = create_application()
