import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint_returns_200(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["environment"] == "development"
    assert data["version"] == "1.0.0"
    assert "timestamp" in data
    assert "services" in data
    assert data["services"]["api"] == "operational"


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient):
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["health"] == "/api/v1/health"


@pytest.mark.asyncio
async def test_unknown_endpoint_returns_404(async_client: AsyncClient):
    response = await async_client.get("/api/v1/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cors_headers_allowed(async_client: AsyncClient):
    response = await async_client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:8081",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
