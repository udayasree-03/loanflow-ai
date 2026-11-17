import sys
from pathlib import Path

# Ensure backend directory is in sys.path when executed directly or from repository root
backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import api_router
from app.core.config import settings
from app.core.logging import setup_logging

logger = logging.getLogger("loanflow.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and shutdown events."""
    setup_logging()
    logger.info("Starting %s v%s in [%s] mode", settings.PROJECT_NAME, settings.VERSION, settings.ENVIRONMENT)
    yield
    logger.info("Shutting down %s", settings.PROJECT_NAME)


def create_application() -> FastAPI:
    """Factory function to build and configure the FastAPI application instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan,
    )

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routes
    app.include_router(api_router, prefix=settings.API_V1_STR)

    @app.get("/", summary="Root Index", include_in_schema=False)
    async def root_index() -> JSONResponse:
        return JSONResponse(
            content={
                "name": settings.PROJECT_NAME,
                "version": settings.VERSION,
                "status": "online",
                "docs_url": f"{settings.API_V1_STR}/docs",
                "health_url": f"{settings.API_V1_STR}/health",
            }
        )

    return app


app = create_application()
