import uuid
from fastapi import APIRouter, Depends, status
from app.api.deps import get_current_user_id
from app.schemas.routing import (
    RouteCalculateRequest,
    RouteCalculateResponse,
)
from app.services.routing_service import RoutingService

router = APIRouter()
routing_service = RoutingService()


@router.post(
    "/calculate",
    response_model=RouteCalculateResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate route distance, duration and geometry",
    description="Calculates route distance and duration using OSRM with full GeoJSON line geometry.",
)
async def calculate_route(
    request: RouteCalculateRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> RouteCalculateResponse:
    return await routing_service.calculate_route(request)
