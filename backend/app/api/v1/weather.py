import uuid
from fastapi import APIRouter, Depends, Query, status
from app.api.deps import get_current_user_id
from app.schemas.weather import WeatherForecastResponse
from app.services.weather_service import WeatherService

router = APIRouter()
weather_service = WeatherService()


@router.get(
    "/forecast",
    response_model=WeatherForecastResponse,
    status_code=status.HTTP_200_OK,
    summary="Get destination weather forecast",
    description="Fetches real-time weather and 7-day daily forecasts via Open-Meteo using destination coordinates.",
)
async def get_forecast(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Destination latitude"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Destination longitude"),
    days: int = Query(7, ge=1, le=14, description="Forecast days (1-14)"),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> WeatherForecastResponse:
    return await weather_service.get_forecast(latitude=lat, longitude=lon, days=days)
