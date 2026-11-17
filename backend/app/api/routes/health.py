import logging
from fastapi import APIRouter
from app.core.config import settings
from app.schemas.health import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="Returns the operational status, current version, and environment of the API service.",
)
async def check_health() -> HealthResponse:
    logger.debug("Health check probe invoked")
    return HealthResponse(
        status="healthy",
        environment=settings.ENVIRONMENT,
        version=settings.VERSION,
    )
