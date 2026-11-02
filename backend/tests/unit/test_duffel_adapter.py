from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
import httpx
import pytest

from app.providers.travel.duffel_adapter import (
    DuffelAdapter,
    DuffelConfigurationError,
    DuffelAuthenticationError,
    DuffelRateLimitError,
    DuffelServiceUnavailableError,
    DuffelValidationError,
    format_duffel_headers,
    parse_iso_duration,
)
from app.schemas.offer import FlightSearchRequest, HotelSearchRequest


def test_duffel_headers_construction():
    headers = format_duffel_headers(access_token="test_token_xyz123", version="v2")
    assert headers["Authorization"] == "Bearer test_token_xyz123"
    assert headers["Duffel-Version"] == "v2"
    assert headers["Accept"] == "application/json"
    assert headers["Content-Type"] == "application/json"
    assert "Travio" in headers["User-Agent"]


def test_duffel_missing_token_raises_configuration_error():
    adapter = DuffelAdapter(access_token="")
    with pytest.raises(DuffelConfigurationError) as exc_info:
        adapter._get_headers()
    assert "DUFFEL_ACCESS_TOKEN is not configured" in str(exc_info.value)


def test_parse_iso_duration_variations():
    h, m = parse_iso_duration("PT7H45M")
    assert h == "7h 45m"
    assert m == 465

    h, m = parse_iso_duration("PT2H")
    assert h == "2h"
    assert m == 120

    h, m = parse_iso_duration("PT30M")
    assert h == "30m"
    assert m == 30

    h, m = parse_iso_duration(None)
    assert h == "N/A"
    assert m == 0


def test_flight_request_payload_construction_one_way():
    adapter = DuffelAdapter(access_token="mock_token")
    req = FlightSearchRequest(
        origin="lhr",
        destination="jfk",
        departure_date=date(2026, 11, 15),
        adults=2,
        children=1,
        cabin_class="economy",
    )
    payload = adapter.build_flight_request_payload(req)
    data = payload["data"]
    assert len(data["slices"]) == 1
    assert data["slices"][0]["origin"] == "LHR"
    assert data["slices"][0]["destination"] == "JFK"
    assert data["slices"][0]["departure_date"] == "2026-11-15"
    assert len(data["passengers"]) == 3
    assert data["cabin_class"] == "economy"


def test_flight_request_payload_construction_round_trip():
    adapter = DuffelAdapter(access_token="mock_token")
    req = FlightSearchRequest(
        origin="LHR",
        destination="HND",
        departure_date=date(2026, 11, 15),
        return_date=date(2026, 11, 25),
        adults=1,
        cabin_class="business",
    )
    payload = adapter.build_flight_request_payload(req)
    slices = payload["data"]["slices"]
    assert len(slices) == 2
    assert slices[0]["origin"] == "LHR"
    assert slices[0]["destination"] == "HND"
    assert slices[1]["origin"] == "HND"
    assert slices[1]["destination"] == "LHR"
    assert slices[1]["departure_date"] == "2026-11-25"
    assert payload["data"]["cabin_class"] == "business"


def test_hotel_request_payload_construction():
    adapter = DuffelAdapter(access_token="mock_token")
    req = HotelSearchRequest(
        latitude=48.8566,
        longitude=2.3522,
        radius_km=15,
        check_in_date=date(2026, 11, 20),
        check_out_date=date(2026, 11, 25),
        rooms=2,
        guests=4,
    )
    payload = adapter.build_hotel_request_payload(req)
    data = payload["data"]
    assert data["location"]["geographic_coordinates"]["latitude"] == 48.8566
    assert data["location"]["geographic_coordinates"]["longitude"] == 2.3522
    assert data["location"]["radius"] == 15
    assert data["check_in_date"] == "2026-11-20"
    assert data["check_out_date"] == "2026-11-25"
    assert data["rooms"] == 2
    assert len(data["guests"]) == 4


@pytest.mark.asyncio
async def test_successful_flight_response_normalization_and_price_preservation():
    mock_duffel_response = {
        "data": {
            "id": "orq_12345",
            "offers": [
                {
                    "id": "off_british_airways_001",
                    "total_amount": "589.45",
                    "total_currency": "GBP",
                    "expires_at": "2026-11-15T18:00:00Z",
                    "owner": {
                        "name": "British Airways",
                        "iata_code": "BA",
                        "logo_symbol_url": "https://assets.duffel.com/img/airlines/for-light-background/full-color-logo/BA.svg",
                    },
                    "slices": [
                        {
                            "id": "sli_001",
                            "duration": "PT8H15M",
                            "segments": [
                                {
                                    "id": "seg_001",
                                    "departing_at": "2026-11-15T09:30:00",
                                    "arriving_at": "2026-11-15T17:45:00",
                                    "stops": [],
                                }
                            ],
                        }
                    ],
                }
            ],
        }
    }

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_http_response = MagicMock(spec=httpx.Response)
    mock_http_response.is_success = True
    mock_http_response.json.return_value = mock_duffel_response
    mock_client.post.return_value = mock_http_response

    adapter = DuffelAdapter(access_token="mock_valid_token", client=mock_client)
    req = FlightSearchRequest(
        origin="LHR",
        destination="JFK",
        departure_date=date(2026, 11, 15),
        adults=1,
    )

    result = await adapter.search_flights(req)
    assert result.total_offers == 1
    offer = result.offers[0]

    # Exact price preservation
    assert offer.price == Decimal("589.45")
    assert offer.currency == "GBP"
    assert offer.provider == "DUFFEL"
    assert offer.provider_offer_id == "off_british_airways_001"
    assert offer.airline_name == "British Airways"
    assert offer.airline_code == "BA"
    assert offer.duration == "8h 15m"
    assert offer.duration_minutes == 495
    assert offer.stops == 0


@pytest.mark.asyncio
async def test_successful_hotel_response_normalization_and_price_preservation():
    mock_duffel_stays_response = {
        "data": {
            "results": [
                {
                    "id": "acc_ritz_paris",
                    "accommodation": {
                        "name": "The Ritz Paris",
                        "rating": 5.0,
                        "location": {
                            "address": {
                                "line_one": "15 Place Vendôme",
                                "city_name": "Paris",
                                "country_code": "FR",
                            },
                            "geographic_coordinates": {
                                "latitude": 48.8682,
                                "longitude": 2.3294,
                            },
                        },
                        "photos": [{"url": "https://images.duffel.com/ritz.jpg"}],
                    },
                    "cheapest_rate_total_amount": "1250.00",
                    "cheapest_rate_currency": "EUR",
                    "rooms": [
                        {
                            "name": "Superior Queen Room",
                            "rates": [
                                {
                                    "id": "rat_superior_queen_01",
                                    "total_amount": "1250.00",
                                    "total_currency": "EUR",
                                    "cancellation_timeline": [
                                        {
                                            "refund_amount": "1250.00",
                                            "currency": "EUR",
                                            "before": "2026-11-18T23:59:59Z",
                                        }
                                    ],
                                    "expires_at": "2026-11-15T12:00:00Z",
                                }
                            ],
                        }
                    ],
                }
            ]
        }
    }

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_http_response = MagicMock(spec=httpx.Response)
    mock_http_response.is_success = True
    mock_http_response.json.return_value = mock_duffel_stays_response
    mock_client.post.return_value = mock_http_response

    adapter = DuffelAdapter(access_token="mock_valid_token", client=mock_client)
    req = HotelSearchRequest(
        latitude=48.8682,
        longitude=2.3294,
        check_in_date=date(2026, 11, 20),
        check_out_date=date(2026, 11, 25),
    )

    result = await adapter.search_hotels(req)
    assert result.total_offers == 1
    offer = result.offers[0]

    assert offer.price == Decimal("1250.00")
    assert offer.currency == "EUR"
    assert offer.accommodation_name == "The Ritz Paris"
    assert offer.latitude == 48.8682
    assert offer.longitude == 2.3294
    assert offer.rating == 5.0
    assert "1250.00 EUR" in (offer.cancellation_policy or "")


@pytest.mark.asyncio
async def test_missing_or_malformed_response_fields_handled_gracefully():
    # Response with an offer missing 'total_amount' and another with valid structure
    mock_response = {
        "data": {
            "offers": [
                {
                    "id": "off_bad_001",
                    # missing total_amount and total_currency
                },
                {
                    "id": "off_good_002",
                    "total_amount": "199.99",
                    "total_currency": "USD",
                    "owner": {"name": "Delta Air Lines", "iata_code": "DL"},
                    "slices": [
                        {
                            "duration": "PT3H30M",
                            "segments": [
                                {
                                    "departing_at": "2026-11-15T08:00:00",
                                    "arriving_at": "2026-11-15T11:30:00",
                                }
                            ],
                        }
                    ],
                },
            ]
        }
    }

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_res = MagicMock(spec=httpx.Response)
    mock_res.is_success = True
    mock_res.json.return_value = mock_response
    mock_client.post.return_value = mock_res

    adapter = DuffelAdapter(access_token="mock_valid_token", client=mock_client)
    req = FlightSearchRequest(
        origin="ATL",
        destination="LGA",
        departure_date=date(2026, 11, 15),
    )

    result = await adapter.search_flights(req)
    assert result.total_offers == 1
    assert result.offers[0].id == "off_good_002"
    assert result.offers[0].price == Decimal("199.99")


@pytest.mark.asyncio
async def test_invalid_credentials_raises_authentication_error():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_res = MagicMock(spec=httpx.Response)
    mock_res.is_success = False
    mock_res.status_code = 401
    mock_res.json.return_value = {
        "errors": [{"title": "Unauthorized", "message": "The access token provided is invalid"}]
    }
    mock_client.post.return_value = mock_res

    adapter = DuffelAdapter(access_token="bad_token", client=mock_client)
    req = FlightSearchRequest(
        origin="JFK",
        destination="LAX",
        departure_date=date(2026, 11, 15),
    )

    with pytest.raises(DuffelAuthenticationError) as exc_info:
        await adapter.search_flights(req)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_rate_limit_exceeded_raises_rate_limit_error():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_res = MagicMock(spec=httpx.Response)
    mock_res.is_success = False
    mock_res.status_code = 429
    mock_res.headers = {"Retry-After": "60"}
    mock_res.json.return_value = {
        "errors": [{"title": "Rate limit exceeded", "message": "Too many requests"}]
    }
    mock_client.post.return_value = mock_res

    adapter = DuffelAdapter(access_token="mock_token", client=mock_client)
    req = FlightSearchRequest(
        origin="JFK",
        destination="LAX",
        departure_date=date(2026, 11, 15),
    )

    with pytest.raises(DuffelRateLimitError) as exc_info:
        await adapter.search_flights(req)
    assert exc_info.value.status_code == 429
    assert exc_info.value.retry_after == 60


@pytest.mark.asyncio
async def test_provider_timeout_and_5xx_raises_service_unavailable_error():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.side_effect = httpx.TimeoutException("Connection timed out")

    adapter = DuffelAdapter(access_token="mock_token", client=mock_client)
    req = FlightSearchRequest(
        origin="JFK",
        destination="LAX",
        departure_date=date(2026, 11, 15),
    )

    with pytest.raises(DuffelServiceUnavailableError) as exc_info:
        await adapter.search_flights(req)
    assert "timed out" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_no_results_returns_empty_offers_without_fake_data():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_res = MagicMock(spec=httpx.Response)
    mock_res.is_success = True
    mock_res.json.return_value = {"data": {"offers": []}}
    mock_client.post.return_value = mock_res

    adapter = DuffelAdapter(access_token="mock_token", client=mock_client)
    req = FlightSearchRequest(
        origin="XYZ",
        destination="ABC",
        departure_date=date(2026, 11, 15),
    )

    result = await adapter.search_flights(req)
    assert result.total_offers == 0
    assert len(result.offers) == 0

