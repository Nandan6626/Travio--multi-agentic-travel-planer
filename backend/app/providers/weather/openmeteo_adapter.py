from typing import List, Optional, Dict
import httpx
from app.schemas.weather import (
    CurrentWeather,
    DailyWeather,
    WeatherForecastResponse,
)

# Standard WMO Weather Interpretation Table
WMO_CODE_MAP: Dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    62: "Moderate rain",
    63: "Heavy rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def interpret_wmo_code(code: int) -> str:
    """Interprets standard WMO weather codes into human-readable descriptions."""
    return WMO_CODE_MAP.get(code, f"Weather condition (code {code})")


class WeatherError(Exception):
    """Base exception for weather provider errors."""
    pass


class InvalidWeatherCoordinateError(WeatherError):
    """Raised when latitude or longitude is invalid."""
    pass


class WeatherServiceUnavailableError(WeatherError):
    """Raised when Open-Meteo is unreachable, timed out, or returning 5xx."""
    pass


class OpenMeteoAdapter:
    """Production adapter for Open-Meteo Weather Forecast API.
    
    Free, reliable, no API key required.
    Fetches real-time observations and 7-day forecasts using coordinates.
    """

    def __init__(
        self,
        base_url: str = "https://api.open-meteo.com",
        timeout_seconds: float = 8.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def get_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 7,
        client: Optional[httpx.AsyncClient] = None,
    ) -> WeatherForecastResponse:
        """Retrieves current weather conditions and daily forecast for destination coordinates."""
        if not (-90.0 <= latitude <= 90.0):
            raise InvalidWeatherCoordinateError(f"Latitude {latitude} is outside valid range [-90, 90].")
        if not (-180.0 <= longitude <= 180.0):
            raise InvalidWeatherCoordinateError(f"Longitude {longitude} is outside valid range [-180, 180].")

        forecast_days = max(1, min(days, 14))
        url = f"{self.base_url}/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "forecast_days": forecast_days,
            "timezone": "auto",
        }

        try:
            if client is not None:
                resp = await client.get(url, params=params, timeout=self.timeout_seconds)
                self._handle_response_errors(resp)
                data = resp.json()
            else:
                async with httpx.AsyncClient() as default_client:
                    resp = await default_client.get(url, params=params, timeout=self.timeout_seconds)
                    self._handle_response_errors(resp)
                    data = resp.json()
        except httpx.TimeoutException as e:
            raise WeatherServiceUnavailableError(f"Open-Meteo weather request timed out: {e}") from e
        except httpx.RequestError as e:
            raise WeatherServiceUnavailableError(f"Open-Meteo connection failed: {e}") from e

        # Extract current weather
        current_data = data.get("current")
        current_weather = None
        if current_data:
            code = int(current_data.get("weather_code", 0))
            current_weather = CurrentWeather(
                temperature_celsius=float(current_data.get("temperature_2m", 0.0)),
                humidity_percent=int(current_data["relative_humidity_2m"]) if "relative_humidity_2m" in current_data else None,
                wind_speed_kmh=float(current_data["wind_speed_10m"]) if "wind_speed_10m" in current_data else None,
                weather_code=code,
                condition=interpret_wmo_code(code),
                timestamp=str(current_data.get("time", "")),
            )

        # Extract daily forecast
        daily_list: List[DailyWeather] = []
        daily_data = data.get("daily", {})
        times = daily_data.get("time", [])
        codes = daily_data.get("weather_code", [])
        max_temps = daily_data.get("temperature_2m_max", [])
        min_temps = daily_data.get("temperature_2m_min", [])
        precip_probs = daily_data.get("precipitation_probability_max", [])

        for idx, date_str in enumerate(times):
            day_code = int(codes[idx]) if idx < len(codes) else 0
            day_max = float(max_temps[idx]) if idx < len(max_temps) else 0.0
            day_min = float(min_temps[idx]) if idx < len(min_temps) else 0.0
            day_precip = int(precip_probs[idx]) if idx < len(precip_probs) and precip_probs[idx] is not None else None

            daily_list.append(
                DailyWeather(
                    date=date_str,
                    weather_code=day_code,
                    condition=interpret_wmo_code(day_code),
                    temp_max_celsius=day_max,
                    temp_min_celsius=day_min,
                    precipitation_probability_percent=day_precip,
                )
            )

        return WeatherForecastResponse(
            latitude=float(data.get("latitude", latitude)),
            longitude=float(data.get("longitude", longitude)),
            timezone=str(data.get("timezone", "UTC")),
            current=current_weather,
            daily=daily_list,
            provider="Open-Meteo",
        )

    def _handle_response_errors(self, response: httpx.Response) -> None:
        if response.is_success:
            return

        status_code = response.status_code
        try:
            error_data = response.json()
            reason = error_data.get("reason") or response.text
        except Exception:
            reason = response.text or f"HTTP {status_code}"

        if status_code in (400, 422):
            raise InvalidWeatherCoordinateError(f"Invalid weather parameters ({status_code}): {reason}")
        elif status_code >= 500:
            raise WeatherServiceUnavailableError(f"Open-Meteo service unavailable ({status_code}): {reason}")
        else:
            raise WeatherError(f"Weather request failed with HTTP {status_code}: {reason}")
