from fastapi import APIRouter
from app.core.config import settings
from app.schemas.common import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check & system diagnostics",
    description="Returns API service health, active environment, and version.",
)
async def get_health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        environment=settings.ENVIRONMENT,
        version=settings.VERSION,
        services={
            "api": "operational",
            "environment": settings.ENVIRONMENT,
        },
    )
