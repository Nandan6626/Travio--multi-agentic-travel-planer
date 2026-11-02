from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import patch
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.offer import SearchRecord, TravelOffer
from app.providers.travel.duffel_adapter import DuffelServiceUnavailableError
from app.schemas.offer import (
    FlightSearchResponse,
    FlightSearchRequest,
    FlightOfferItem,
    HotelSearchResponse,
    HotelSearchRequest,
    HotelOfferItem,
)
from tests.conftest import create_test_jwt


@pytest.mark.asyncio
async def test_search_flights_api_and_database_persistence(async_client: AsyncClient, db_session: AsyncSession):
    user_id = uuid.uuid4()
    token = create_test_jwt(user_id=user_id)
    headers = {"Authorization": f"Bearer {token}"}

    dep_date = date.today() + timedelta(days=30)
    req_data = {
        "origin": "LHR",
        "destination": "JFK",
        "departure_date": str(dep_date),
        "adults": 1,
        "cabin_class": "economy",
    }

    mock_flight_offer = FlightOfferItem(
        id="off_test_flight_123",
        provider="DUFFEL",
        provider_offer_id="off_test_flight_123",
        airline_name="Virgin Atlantic",
        airline_code="VS",
        price=Decimal("485.50"),
        currency="USD",
        departure_time=datetime.now(timezone.utc) + timedelta(days=30),
        arrival_time=datetime.now(timezone.utc) + timedelta(days=30, hours=8),
        duration="8h 0m",
        duration_minutes=480,
        stops=0,
        passengers_count=1,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
    )

    mock_response = FlightSearchResponse(
        provider="DUFFEL",
        total_offers=1,
        query=FlightSearchRequest(**req_data),
        offers=[mock_flight_offer],
    )

    with patch("app.api.v1.offers.travel_service.adapter.search_flights", return_value=mock_response):
        res = await async_client.post("/api/v1/offers/flights/search", headers=headers, json=req_data)

    assert res.status_code == 200
    data = res.json()
    assert data["provider"] == "DUFFEL"
    assert data["total_offers"] == 1
    assert data["offers"][0]["price"] == "485.50"
    assert data["offers"][0]["currency"] == "USD"
    assert data["offers"][0]["airline_name"] == "Virgin Atlantic"

    # Verify search record and offer were persisted to database
    rec_res = await db_session.execute(select(SearchRecord).where(SearchRecord.search_type == "FLIGHT"))
    records = list(rec_res.scalars().all())
    assert len(records) >= 1

    offer_res = await db_session.execute(
        select(TravelOffer).where(TravelOffer.provider_offer_id == "off_test_flight_123")
    )
    saved_offer = offer_res.scalar_one_or_none()
    assert saved_offer is not None
    assert saved_offer.provider_name == "DUFFEL"
    assert saved_offer.verified_price == Decimal("485.50")
    assert saved_offer.currency == "USD"


@pytest.mark.asyncio
async def test_search_hotels_api_and_database_persistence(async_client: AsyncClient, db_session: AsyncSession):
    user_id = uuid.uuid4()
    token = create_test_jwt(user_id=user_id)
    headers = {"Authorization": f"Bearer {token}"}

    check_in = date.today() + timedelta(days=20)
    check_out = date.today() + timedelta(days=25)
    req_data = {
        "latitude": 48.8566,
        "longitude": 2.3522,
        "radius_km": 15,
        "check_in_date": str(check_in),
        "check_out_date": str(check_out),
        "rooms": 1,
        "guests": 2,
    }

    mock_hotel_offer = HotelOfferItem(
        id="rat_paris_boutique_001",
        provider="DUFFEL",
        provider_offer_id="rat_paris_boutique_001",
        accommodation_name="Hôtel Le Marais",
        address="12 Rue des Francs-Bourgeois, Paris",
        latitude=48.8575,
        longitude=2.3590,
        rating=4.6,
        room_name="Classic Double",
        price=Decimal("620.00"),
        currency="EUR",
        cancellation_policy="Free cancellation before check-in",
        check_in_date=check_in,
        check_out_date=check_out,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=3),
    )

    mock_response = HotelSearchResponse(
        provider="DUFFEL",
        total_offers=1,
        query=HotelSearchRequest(**req_data),
        offers=[mock_hotel_offer],
    )

    with patch("app.api.v1.offers.travel_service.adapter.search_hotels", return_value=mock_response):
        res = await async_client.post("/api/v1/offers/hotels/search", headers=headers, json=req_data)

    assert res.status_code == 200
    data = res.json()
    assert data["provider"] == "DUFFEL"
    assert data["total_offers"] == 1
    assert data["offers"][0]["price"] == "620.00"
    assert data["offers"][0]["currency"] == "EUR"
    assert data["offers"][0]["accommodation_name"] == "Hôtel Le Marais"


@pytest.mark.asyncio
async def test_get_stored_travel_offer_and_expiration_detection(
    async_client: AsyncClient, db_session: AsyncSession
):
    user_id = uuid.uuid4()
    token = create_test_jwt(user_id=user_id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Active Offer
    active_offer = TravelOffer(
        provider_name="DUFFEL",
        offer_type="FLIGHT",
        provider_offer_id="off_active_999",
        verified_price=Decimal("350.00"),
        currency="USD",
        valid_until=datetime.now(timezone.utc) + timedelta(hours=1),
        offer_details={"airline": "United Airlines", "flight_no": "UA100"},
    )
    # 2. Expired Offer
    expired_offer = TravelOffer(
        provider_name="DUFFEL",
        offer_type="HOTEL",
        provider_offer_id="rat_expired_888",
        verified_price=Decimal("200.00"),
        currency="USD",
        valid_until=datetime.now(timezone.utc) - timedelta(hours=2),
        offer_details={"hotel": "Past Stay Inn"},
    )
    db_session.add(active_offer)
    db_session.add(expired_offer)
    await db_session.commit()

    # Query active
    res_active = await async_client.get(f"/api/v1/offers/{active_offer.id}", headers=headers)
    assert res_active.status_code == 200
    data_active = res_active.json()
    assert data_active["is_expired"] is False
    assert data_active["is_provider_verified"] is True
    assert data_active["verified_price"] == "350.00"

    # Query expired
    res_exp = await async_client.get(f"/api/v1/offers/{expired_offer.id}", headers=headers)
    assert res_exp.status_code == 200
    data_exp = res_exp.json()
    assert data_exp["is_expired"] is True
    assert data_exp["verified_price"] == "200.00"


@pytest.mark.asyncio
async def test_provider_unavailable_returns_503(async_client: AsyncClient):
    user_id = uuid.uuid4()
    token = create_test_jwt(user_id=user_id)
    headers = {"Authorization": f"Bearer {token}"}

    with patch(
        "app.api.v1.offers.travel_service.adapter.search_flights",
        side_effect=DuffelServiceUnavailableError("Duffel service timeout"),
    ):
        res = await async_client.post(
            "/api/v1/offers/flights/search",
            headers=headers,
            json={
                "origin": "LHR",
                "destination": "JFK",
                "departure_date": str(date.today() + timedelta(days=10)),
            },
        )
    assert res.status_code == 503
    assert "unavailable" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_unauthenticated_offers_access_returns_401(async_client: AsyncClient):
    res = await async_client.post(
        "/api/v1/offers/flights/search",
        json={"origin": "LHR", "destination": "JFK", "departure_date": "2026-11-20"},
    )
    assert res.status_code == 401

