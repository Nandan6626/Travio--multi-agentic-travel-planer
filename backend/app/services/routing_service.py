from typing import Optional
from fastapi import HTTPException, status
from app.schemas.routing import (
    RouteCalculateRequest,
    RouteCalculateResponse,
)
from app.providers.routing.osrm_adapter import (
    RoutingAdapterInterface,
    OSRMAdapter,
    InvalidCoordinateError,
    RouteNotFoundError,
    RoutingServiceUnavailableError,
    RoutingError,
)
from app.core.logging import logger


class RoutingService:
    def __init__(self, adapter: Optional[RoutingAdapterInterface] = None):
        self.adapter = adapter or OSRMAdapter()

    async def calculate_route(
        self,
        request: RouteCalculateRequest,
    ) -> RouteCalculateResponse:
        """Calculates distance, duration, and geometry between coordinates."""
        try:
            return await self.adapter.calculate_route(request)
        except InvalidCoordinateError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e),
            )
        except RouteNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        except RoutingServiceUnavailableError as e:
            logger.error(f"Routing service unavailable: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Routing service temporarily unavailable: {e}",
            )
        except RoutingError as e:
            logger.error(f"Routing calculation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Routing calculation failed: {e}",
            )
