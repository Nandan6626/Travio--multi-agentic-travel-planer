from typing import List, Optional
from pydantic import BaseModel, Field


class CurrentWeather(BaseModel):
    temperature_celsius: float = Field(..., description="Current ambient temperature in Celsius")
    humidity_percent: Optional[int] = Field(None, description="Current relative humidity percentage")
    wind_speed_kmh: Optional[float] = Field(None, description="Wind speed in km/h")
    weather_code: int = Field(..., description="WMO standard weather condition code")
    condition: str = Field(..., description="Human-readable condition description (e.g. Sunny, Light rain)")
    timestamp: str = Field(..., description="ISO 8601 observation timestamp")


class DailyWeather(BaseModel):
    date: str = Field(..., description="Forecast date (YYYY-MM-DD)")
    weather_code: int = Field(..., description="Primary WMO weather code for the day")
    condition: str = Field(..., description="Human-readable condition summary")
    temp_max_celsius: float = Field(..., description="Maximum forecasted temperature in Celsius")
    temp_min_celsius: float = Field(..., description="Minimum forecasted temperature in Celsius")
    precipitation_probability_percent: Optional[int] = Field(
        None, description="Maximum probability of precipitation (0-100%)"
    )


class WeatherForecastResponse(BaseModel):
    latitude: float = Field(..., description="Latitude of forecast location")
    longitude: float = Field(..., description="Longitude of forecast location")
    timezone: str = Field(default="UTC", description="Resolved local timezone")
    current: Optional[CurrentWeather] = Field(None, description="Current weather conditions")
    daily: List[DailyWeather] = Field(default_factory=list, description="Day-by-day forecast list")
    provider: str = Field(default="Open-Meteo", description="Authoritative weather provider name")
