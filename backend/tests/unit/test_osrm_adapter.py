import pytest
import httpx
from app.providers.routing.osrm_adapter import (
    OSRMAdapter,
    InvalidCoordinateError,
    RouteNotFoundError,
    RoutingServiceUnavailableError,
)
from app.schemas.routing import Coordinate, RouteCalculateRequest


@pytest.fixture
def adapter():
    return OSRMAdapter(base_url="https://router.project-osrm.org")


@pytest.mark.asyncio
async def test_osrm_coordinate_boundary_validation(adapter):
    # Invalid origin lat bypassing pydantic init
    req = RouteCalculateRequest(
        origin=Coordinate.model_construct(latitude=95.0, longitude=2.35),
        destination=Coordinate(latitude=48.85, longitude=2.35),
    )
    with pytest.raises(InvalidCoordinateError):
        await adapter.calculate_route(req)

    # Invalid destination lon bypassing pydantic init
    req2 = RouteCalculateRequest(
        origin=Coordinate(latitude=48.85, longitude=2.35),
        destination=Coordinate.model_construct(latitude=48.85, longitude=185.0),
    )
    with pytest.raises(InvalidCoordinateError):
        await adapter.calculate_route(req2)


@pytest.mark.asyncio
async def test_osrm_successful_route_calculation(adapter):
    mock_payload = {
        "code": "Ok",
        "routes": [
            {
                "distance": 4500.5,
                "duration": 600.0,
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[2.3522, 48.8566], [2.2945, 48.8584]],
                },
                "legs": [
                    {
                        "distance": 4500.5,
                        "duration": 600.0,
                        "summary": "Boulevard Saint-Germain",
                    }
                ],
            }
        ],
    }

    async def mock_handler(request: httpx.Request):
        assert "2.3522,48.8566;2.2945,48.8584" in str(request.url)
        return httpx.Response(200, json=mock_payload)

    transport = httpx.MockTransport(mock_handler)
    req = RouteCalculateRequest(
        origin=Coordinate(latitude=48.8566, longitude=2.3522),
        destination=Coordinate(latitude=48.8584, longitude=2.2945),
        profile="driving",
    )

    async with httpx.AsyncClient(transport=transport) as client:
        result = await adapter.calculate_route(req, client=client)

    assert result.distance_meters == 4500.5
    assert result.distance_km == 4.5
    assert result.duration_seconds == 600.0
    assert result.duration_minutes == 10.0
    assert result.is_traffic_adjusted is False
    assert result.geometry is not None
    assert len(result.geometry.coordinates) == 2
    assert len(result.legs) == 1
    assert result.legs[0].summary == "Boulevard Saint-Germain"


@pytest.mark.asyncio
async def test_osrm_route_not_found(adapter):
    mock_payload = {"code": "NoRoute", "routes": []}
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=mock_payload))) as client:
        req = RouteCalculateRequest(
            origin=Coordinate(latitude=0.0, longitude=0.0),
            destination=Coordinate(latitude=50.0, longitude=50.0),
        )
        with pytest.raises(RouteNotFoundError):
            await adapter.calculate_route(req, client=client)


@pytest.mark.asyncio
async def test_osrm_service_unavailable(adapter):
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(503, text="Service down"))) as client:
        req = RouteCalculateRequest(
            origin=Coordinate(latitude=48.8566, longitude=2.3522),
            destination=Coordinate(latitude=48.8584, longitude=2.2945),
        )
        with pytest.raises(RoutingServiceUnavailableError):
            await adapter.calculate_route(req, client=client)
