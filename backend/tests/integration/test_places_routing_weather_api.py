import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.api.v1.places import place_service
from app.api.v1.routes import routing_service
from app.api.v1.weather import weather_service
from app.schemas.place import PlaceSearchResult, DestinationSearchResult
from app.schemas.routing import RouteCalculateResponse, RouteGeometry, RouteLeg
from app.schemas.weather import WeatherForecastResponse, CurrentWeather, DailyWeather
from tests.conftest import create_test_jwt


@pytest.fixture
def auth_headers():
    user_id = uuid.uuid4()
    token = create_test_jwt(user_id=user_id)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_places_search_and_cache_api(auth_headers, monkeypatch):
    # Mock Geoapify adapter methods
    mock_destination = DestinationSearchResult(
        name="Paris",
        formatted_address="Paris, France",
        latitude=48.8566,
        longitude=2.3522,
        place_id="dest-paris-1",
    )
    mock_place = PlaceSearchResult(
        provider_id="geo-eiffel-123",
        name="Eiffel Tower",
        address="Champ de Mars, 5 Av. Anatole France, 75007 Paris",
        latitude=48.8584,
        longitude=2.2945,
        category="tourism.attraction",
        categories=["tourism.attraction"],
        rating=4.7,
        opening_hours={"open_now": True},
        website="https://www.toureiffel.paris",
    )

    async def mock_search_destination(query, limit=5, client=None):
        return [mock_destination]

    async def mock_search_places(lat, lon, categories, radius_meters=5000, limit=20, name=None, client=None):
        return [mock_place]

    async def mock_get_place_details(place_id, client=None):
        if place_id == "geo-eiffel-123":
            return mock_place
        return None

    monkeypatch.setattr(place_service.adapter, "search_destination", mock_search_destination)
    monkeypatch.setattr(place_service.adapter, "search_places", mock_search_places)
    monkeypatch.setattr(place_service.adapter, "get_place_details", mock_get_place_details)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Search places by text
        res = await client.get("/api/v1/places/search?text=Paris", headers=auth_headers)
        assert res.status_code == 200
        places = res.json()
        assert len(places) == 1
        assert places[0]["name"] == "Eiffel Tower"
        assert places[0]["provider_id"] == "geo-eiffel-123"
        assert places[0]["is_cached"] is False

        # Retrieve place details by provider_id (should auto-cache into DB)
        res2 = await client.get("/api/v1/places/geo-eiffel-123", headers=auth_headers)
        assert res2.status_code == 200
        cached_place = res2.json()
        assert cached_place["name"] == "Eiffel Tower"
        assert cached_place["provider_id"] == "geo-eiffel-123"
        assert "id" in cached_place
        place_uuid = cached_place["id"]

        # Retrieve again by internal UUID
        res3 = await client.get(f"/api/v1/places/{place_uuid}", headers=auth_headers)
        assert res3.status_code == 200
        assert res3.json()["id"] == place_uuid


@pytest.mark.asyncio
async def test_route_calculation_api(auth_headers, monkeypatch):
    mock_route = RouteCalculateResponse(
        distance_meters=5000.0,
        distance_km=5.0,
        duration_seconds=720.0,
        duration_minutes=12.0,
        is_traffic_adjusted=False,
        geometry=RouteGeometry(type="LineString", coordinates=[[2.3522, 48.8566], [2.2945, 48.8584]]),
        legs=[RouteLeg(distance_meters=5000.0, duration_seconds=720.0, summary="Main Road")],
        profile="driving",
        provider="OSRM",
    )

    async def mock_calculate_route(request, client=None):
        return mock_route

    monkeypatch.setattr(routing_service.adapter, "calculate_route", mock_calculate_route)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "origin": {"latitude": 48.8566, "longitude": 2.3522, "name": "Start"},
            "destination": {"latitude": 48.8584, "longitude": 2.2945, "name": "End"},
            "profile": "driving",
        }
        res = await client.post("/api/v1/routes/calculate", json=payload, headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["distance_meters"] == 5000.0
        assert data["distance_km"] == 5.0
        assert data["duration_minutes"] == 12.0
        assert data["is_traffic_adjusted"] is False
        assert data["provider"] == "OSRM"


@pytest.mark.asyncio
async def test_weather_forecast_api(auth_headers, monkeypatch):
    mock_weather = WeatherForecastResponse(
        latitude=48.85,
        longitude=2.35,
        timezone="Europe/Paris",
        current=CurrentWeather(
            temperature_celsius=18.5,
            humidity_percent=55,
            wind_speed_kmh=10.0,
            weather_code=0,
            condition="Clear sky",
            timestamp="2026-11-03T14:00",
        ),
        daily=[
            DailyWeather(
                date="2026-11-03",
                weather_code=0,
                condition="Clear sky",
                temp_max_celsius=20.0,
                temp_min_celsius=12.0,
                precipitation_probability_percent=0,
            )
        ],
        provider="Open-Meteo",
    )

    async def mock_get_forecast(latitude, longitude, days=7, client=None):
        return mock_weather

    monkeypatch.setattr(weather_service.adapter, "get_forecast", mock_get_forecast)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/weather/forecast?lat=48.85&lon=2.35&days=3", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["current"]["temperature_celsius"] == 18.5
        assert data["current"]["condition"] == "Clear sky"
        assert len(data["daily"]) == 1
        assert data["daily"][0]["temp_max_celsius"] == 20.0


@pytest.mark.asyncio
async def test_unauthenticated_milestone4_endpoints_return_401():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Places search
        res1 = await client.get("/api/v1/places/search?text=Paris")
        assert res1.status_code == 401

        # Routes calculate
        res2 = await client.post("/api/v1/routes/calculate", json={
            "origin": {"latitude": 0, "longitude": 0},
            "destination": {"latitude": 1, "longitude": 1},
        })
        assert res2.status_code == 401

        # Weather forecast
        res3 = await client.get("/api/v1/weather/forecast?lat=0&lon=0")
        assert res3.status_code == 401
