from typing import Optional
from fastapi import HTTPException, status
from app.schemas.weather import WeatherForecastResponse
from app.providers.weather.openmeteo_adapter import (
    OpenMeteoAdapter,
    InvalidWeatherCoordinateError,
    WeatherServiceUnavailableError,
    WeatherError,
)
from app.core.logging import logger


class WeatherService:
    def __init__(self, adapter: Optional[OpenMeteoAdapter] = None):
        self.adapter = adapter or OpenMeteoAdapter()

    async def get_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 7,
    ) -> WeatherForecastResponse:
        """Retrieves verified weather observations and daily forecasts."""
        try:
            return await self.adapter.get_forecast(latitude=latitude, longitude=longitude, days=days)
        except InvalidWeatherCoordinateError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e),
            )
        except WeatherServiceUnavailableError as e:
            logger.error(f"Weather service unavailable: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Weather service temporarily unavailable: {e}",
            )
        except WeatherError as e:
            logger.error(f"Weather fetch error: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Weather retrieval failed: {e}",
            )
