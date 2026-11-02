import pytest
import httpx
from app.providers.weather.openmeteo_adapter import (
    OpenMeteoAdapter,
    InvalidWeatherCoordinateError,
    WeatherServiceUnavailableError,
    interpret_wmo_code,
)


@pytest.fixture
def adapter():
    return OpenMeteoAdapter(base_url="https://api.open-meteo.com")


def test_wmo_code_interpretation():
    assert interpret_wmo_code(0) == "Clear sky"
    assert interpret_wmo_code(2) == "Partly cloudy"
    assert interpret_wmo_code(61) == "Slight rain"
    assert interpret_wmo_code(95) == "Thunderstorm"
    assert "code 999" in interpret_wmo_code(999)


@pytest.mark.asyncio
async def test_openmeteo_coordinate_validation(adapter):
    with pytest.raises(InvalidWeatherCoordinateError):
        await adapter.get_forecast(latitude=91.0, longitude=2.35)

    with pytest.raises(InvalidWeatherCoordinateError):
        await adapter.get_forecast(latitude=48.85, longitude=-181.0)


@pytest.mark.asyncio
async def test_openmeteo_successful_forecast_normalization(adapter):
    mock_payload = {
        "latitude": 48.85,
        "longitude": 2.35,
        "timezone": "Europe/Paris",
        "current": {
            "time": "2026-11-03T12:00",
            "temperature_2m": 15.2,
            "relative_humidity_2m": 60,
            "weather_code": 1,
            "wind_speed_10m": 12.5,
        },
        "daily": {
            "time": ["2026-11-03", "2026-11-04"],
            "weather_code": [1, 61],
            "temperature_2m_max": [16.0, 14.5],
            "temperature_2m_min": [9.0, 8.2],
            "precipitation_probability_max": [10, 75],
        },
    }

    transport = httpx.MockTransport(lambda r: httpx.Response(200, json=mock_payload))
    async with httpx.AsyncClient(transport=transport) as client:
        result = await adapter.get_forecast(latitude=48.85, longitude=2.35, client=client)

    assert result.latitude == 48.85
    assert result.longitude == 2.35
    assert result.timezone == "Europe/Paris"
    assert result.provider == "Open-Meteo"

    # Current
    assert result.current is not None
    assert result.current.temperature_celsius == 15.2
    assert result.current.humidity_percent == 60
    assert result.current.wind_speed_kmh == 12.5
    assert result.current.weather_code == 1
    assert result.current.condition == "Mainly clear"

    # Daily
    assert len(result.daily) == 2
    assert result.daily[0].date == "2026-11-03"
    assert result.daily[0].condition == "Mainly clear"
    assert result.daily[0].temp_max_celsius == 16.0
    assert result.daily[0].precipitation_probability_percent == 10

    assert result.daily[1].date == "2026-11-04"
    assert result.daily[1].condition == "Slight rain"
    assert result.daily[1].precipitation_probability_percent == 75


@pytest.mark.asyncio
async def test_openmeteo_service_unavailable(adapter):
    transport = httpx.MockTransport(lambda r: httpx.Response(500, text="Internal Error"))
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(WeatherServiceUnavailableError):
            await adapter.get_forecast(latitude=48.85, longitude=2.35, client=client)
