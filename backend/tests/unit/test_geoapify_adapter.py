import pytest
import httpx
from app.providers.places.geoapify_adapter import (
    GeoapifyAdapter,
    GeoapifyAuthenticationError,
    GeoapifyRateLimitError,
    GeoapifyServiceUnavailableError,
    GeoapifyValidationError,
)


@pytest.fixture
def adapter():
    return GeoapifyAdapter(api_key="test-geoapify-key", base_url="https://api.geoapify.com")


@pytest.mark.asyncio
async def test_geoapify_missing_key_raises_auth_error():
    empty_adapter = GeoapifyAdapter(api_key="")
    with pytest.raises(GeoapifyAuthenticationError) as exc_info:
        await empty_adapter.search_destination("Paris")
    assert "not configured" in str(exc_info.value)


@pytest.mark.asyncio
async def test_search_destination_normalization(adapter):
    mock_payload = {
        "features": [
            {
                "properties": {
                    "name": "Paris",
                    "formatted": "Paris, IDF, France",
                    "country": "France",
                    "country_code": "fr",
                    "lat": 48.8534,
                    "lon": 2.3483,
                    "place_id": "geo-paris-123",
                }
            }
        ]
    }

    async def mock_handler(request: httpx.Request):
        assert request.url.params["text"] == "Paris"
        assert request.url.params["apiKey"] == "test-geoapify-key"
        return httpx.Response(200, json=mock_payload)

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        results = await adapter.search_destination("Paris", client=client)

    assert len(results) == 1
    dest = results[0]
    assert dest.name == "Paris"
    assert dest.latitude == 48.8534
    assert dest.longitude == 2.3483
    assert dest.country_code == "FR"
    assert dest.place_id == "geo-paris-123"


@pytest.mark.asyncio
async def test_search_places_normalization_and_ratings(adapter):
    mock_payload = {
        "features": [
            {
                "properties": {
                    "name": "Louvre Museum",
                    "formatted": "Rue de Rivoli, 75001 Paris, France",
                    "lat": 48.8606,
                    "lon": 2.3376,
                    "categories": ["tourism.attraction", "entertainment.museum"],
                    "rating": 4.8,
                    "opening_hours": {"open_now": True},
                    "website": "https://www.louvre.fr",
                    "place_id": "geo-louvre-456",
                }
            },
            {
                "properties": {
                    "address_line1": "Unnamed Monument",
                    "lat": 48.8500,
                    "lon": 2.3400,
                    "categories": ["tourism.attraction"],
                    "place_id": "geo-monument-789",
                }
            },
        ]
    }

    async def mock_handler(request: httpx.Request):
        assert "circle:2.3522,48.8566,3000" in request.url.params["filter"]
        return httpx.Response(200, json=mock_payload)

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        results = await adapter.search_places(
            lat=48.8566,
            lon=2.3522,
            categories="tourism.attraction",
            radius_meters=3000,
            client=client,
        )

    assert len(results) == 2
    louvre = results[0]
    assert louvre.name == "Louvre Museum"
    assert louvre.rating == 4.8
    assert louvre.opening_hours == {"open_now": True}
    assert louvre.website == "https://www.louvre.fr"

    unnamed = results[1]
    assert unnamed.name == "Unnamed Monument"
    assert unnamed.rating is None
    assert unnamed.opening_hours is None


@pytest.mark.asyncio
async def test_geoapify_error_handling_401_429_500(adapter):
    # 401 Unauthorized
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(401, json={"message": "Invalid API Key"}))) as client:
        with pytest.raises(GeoapifyAuthenticationError):
            await adapter.search_destination("Tokyo", client=client)

    # 429 Rate Limit
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(429, headers={"Retry-After": "30"}, json={"message": "Quota exceeded"}))) as client:
        with pytest.raises(GeoapifyRateLimitError) as exc_info:
            await adapter.search_destination("Tokyo", client=client)
        assert exc_info.value.retry_after == 30

    # 500 Service Unavailable
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(500, text="Internal Error"))) as client:
        with pytest.raises(GeoapifyServiceUnavailableError):
            await adapter.search_destination("Tokyo", client=client)
