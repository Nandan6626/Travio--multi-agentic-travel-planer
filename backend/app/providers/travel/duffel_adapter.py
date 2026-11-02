import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.schemas.offer import (
    FlightSearchRequest,
    FlightOfferItem,
    FlightSearchResponse,
    HotelSearchRequest,
    HotelOfferItem,
    HotelSearchResponse,
)


class DuffelError(Exception):
    """Base exception for all Duffel provider operations."""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


class DuffelConfigurationError(DuffelError):
    """Raised when Duffel API token or configuration is missing or invalid."""
    pass


class DuffelAuthenticationError(DuffelError):
    """Raised when Duffel returns HTTP 401 Unauthorized or 403 Forbidden."""
    pass


class DuffelRateLimitError(DuffelError):
    """Raised when Duffel returns HTTP 429 Too Many Requests."""
    def __init__(self, message: str, retry_after: Optional[int] = None, details: Optional[Any] = None):
        super().__init__(message, status_code=429, details=details)
        self.retry_after = retry_after


class DuffelServiceUnavailableError(DuffelError):
    """Raised when Duffel API is unreachable, times out, or returns 5xx."""
    pass


class DuffelValidationError(DuffelError):
    """Raised when Duffel returns 400 or 422 with invalid search parameters."""
    pass


def parse_iso_duration(iso_str: Optional[str]) -> Tuple[str, int]:
    """
    Parses ISO 8601 duration string like 'PT7H45M' or 'PT2H' into
    a human-readable string ('7h 45m') and integer total minutes (465).
    """
    if not iso_str or not isinstance(iso_str, str):
        return "N/A", 0

    hours = 0
    minutes = 0

    h_match = re.search(r"(\d+)H", iso_str)
    if h_match:
        hours = int(h_match.group(1))

    m_match = re.search(r"(\d+)M", iso_str)
    if m_match:
        minutes = int(m_match.group(1))

    total_mins = hours * 60 + minutes

    if hours > 0 and minutes > 0:
        human_str = f"{hours}h {minutes}m"
    elif hours > 0:
        human_str = f"{hours}h"
    elif minutes > 0:
        human_str = f"{minutes}m"
    else:
        human_str = "0m"

    return human_str, total_mins


def format_duffel_headers(access_token: str, version: str = "v2") -> Dict[str, str]:
    """Constructs official Duffel API authorization and version headers."""
    clean_token = access_token.strip() if access_token else ""
    return {
        "Authorization": f"Bearer {clean_token}",
        "Duffel-Version": version,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Travio-AI/1.0",
    }


class DuffelAdapter:
    """
    Primary travel provider adapter communicating with Duffel Flights and Stays APIs.
    Authenticates via Bearer token, enforces version headers, handles errors,
    and normalizes provider responses into Travio schemas with zero price fabrication.
    """

    def __init__(
        self,
        access_token: Optional[str] = None,
        api_url: Optional[str] = None,
        version: Optional[str] = None,
        client: Optional[httpx.AsyncClient] = None,
        timeout: float = 15.0,
    ):
        self.access_token = access_token if access_token is not None else settings.DUFFEL_ACCESS_TOKEN
        self.api_url = (api_url if api_url is not None else settings.DUFFEL_API_URL).rstrip("/")
        self.version = version if version is not None else settings.DUFFEL_VERSION
        self._custom_client = client
        self.timeout = timeout

    def _get_headers(self) -> Dict[str, str]:
        if not self.access_token or not self.access_token.strip():
            raise DuffelConfigurationError(
                "DUFFEL_ACCESS_TOKEN is not configured. Please set a valid access token in environment variables."
            )
        return format_duffel_headers(self.access_token, self.version)

    def _handle_http_error(self, response: httpx.Response, endpoint: str) -> None:
        """Translates Duffel HTTP error responses to domain-specific exceptions."""
        status_code = response.status_code
        try:
            error_json = response.json()
            errors = error_json.get("errors", [])
            first_err = errors[0] if errors else {}
            err_msg = first_err.get("message") or first_err.get("title") or response.text
        except Exception:
            err_msg = response.text or f"HTTP {status_code}"

        logger.error(f"Duffel API Error on {endpoint}: HTTP {status_code} - {err_msg}")

        if status_code in (401, 403):
            raise DuffelAuthenticationError(
                f"Duffel authentication failed (HTTP {status_code}): Invalid or unauthorized access token.",
                status_code=status_code,
                details=err_msg,
            )
        elif status_code == 429:
            retry_after_hdr = response.headers.get("Retry-After")
            retry_after = int(retry_after_hdr) if retry_after_hdr and retry_after_hdr.isdigit() else None
            raise DuffelRateLimitError(
                "Duffel API rate limit exceeded. Please try again shortly.",
                retry_after=retry_after,
                details=err_msg,
            )
        elif status_code in (400, 422):
            raise DuffelValidationError(
                f"Invalid search parameters rejected by Duffel: {err_msg}",
                status_code=status_code,
                details=err_msg,
            )
        elif status_code >= 500:
            raise DuffelServiceUnavailableError(
                f"Duffel service currently unavailable (HTTP {status_code}). Please retry later.",
                status_code=status_code,
                details=err_msg,
            )
        else:
            raise DuffelError(
                f"Unexpected error from Duffel (HTTP {status_code}): {err_msg}",
                status_code=status_code,
                details=err_msg,
            )

    # --- FLIGHT SEARCH ---

    def build_flight_request_payload(self, request: FlightSearchRequest) -> Dict[str, Any]:
        """Constructs official Duffel Air Offer Request JSON body."""
        slices = [
            {
                "origin": request.origin.strip().upper(),
                "destination": request.destination.strip().upper(),
                "departure_date": str(request.departure_date),
            }
        ]

        if request.return_date:
            slices.append(
                {
                    "origin": request.destination.strip().upper(),
                    "destination": request.origin.strip().upper(),
                    "departure_date": str(request.return_date),
                }
            )

        passengers = [{"type": "adult"} for _ in range(request.adults)]
        for _ in range(request.children):
            passengers.append({"type": "child"})

        return {
            "data": {
                "slices": slices,
                "passengers": passengers,
                "cabin_class": request.cabin_class,
            }
        }

    def normalize_flight_offer(self, offer: Dict[str, Any], total_passengers: int) -> Optional[FlightOfferItem]:
        """Normalizes a single Duffel flight offer into Travio's FlightOfferItem schema."""
        offer_id = offer.get("id")
        total_amount = offer.get("total_amount")
        total_currency = offer.get("total_currency")

        if not offer_id or total_amount is None or not total_currency:
            logger.warning(f"Skipping malformed flight offer: missing id or price ({offer})")
            return None

        # Price accuracy: parse exact Decimal, preserve currency
        try:
            price = Decimal(str(total_amount))
        except Exception:
            return None

        owner = offer.get("owner") or {}
        airline_name = owner.get("name") or "Airline"
        airline_code = owner.get("iata_code")
        airline_logo = owner.get("logo_symbol_url")

        # Parse slices and segments
        slices = offer.get("slices") or []
        first_slice = slices[0] if slices else {}
        segments = first_slice.get("segments") or []

        if not segments:
            logger.warning(f"Skipping flight offer {offer_id}: no segments found")
            return None

        first_seg = segments[0]
        last_seg = segments[-1]

        # Departure and arrival datetimes
        try:
            dep_time = datetime.fromisoformat(first_seg.get("departing_at", ""))
        except Exception:
            dep_time = datetime.now(timezone.utc)

        try:
            arr_time = datetime.fromisoformat(last_seg.get("arriving_at", ""))
        except Exception:
            arr_time = dep_time

        # Duration parsing
        raw_duration = first_slice.get("duration")
        duration_human, duration_mins = parse_iso_duration(raw_duration)

        # Stops count: number of segments in first slice - 1 + intermediate stops
        stops_count = max(0, len(segments) - 1)
        for seg in segments:
            stops_count += len(seg.get("stops") or [])

        # Expiration
        expires_at = None
        raw_exp = offer.get("expires_at")
        if raw_exp:
            try:
                expires_at = datetime.fromisoformat(raw_exp.replace("Z", "+00:00"))
            except Exception:
                pass

        return FlightOfferItem(
            id=str(offer_id),
            provider="DUFFEL",
            provider_offer_id=str(offer_id),
            airline_name=airline_name,
            airline_code=airline_code,
            airline_logo_url=airline_logo,
            price=price,
            currency=str(total_currency).upper(),
            departure_time=dep_time,
            arrival_time=arr_time,
            duration=duration_human,
            duration_minutes=duration_mins,
            stops=stops_count,
            slices=slices,
            passengers_count=total_passengers,
            expires_at=expires_at,
            retrieved_at=datetime.utcnow(),
        )

    async def search_flights(self, request: FlightSearchRequest) -> FlightSearchResponse:
        """
        Executes flight search via Duffel's Offer Requests API (`POST /air/offer_requests`).
        Returns normalized offers or raises a domain exception on failure.
        """
        headers = self._get_headers()
        payload = self.build_flight_request_payload(request)
        url = f"{self.api_url}/air/offer_requests?return_offers=true"

        total_passengers = request.adults + request.children

        try:
            if self._custom_client:
                response = await self._custom_client.post(
                    url, json=payload, headers=headers, timeout=self.timeout
                )
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload, headers=headers)
        except httpx.TimeoutException as e:
            logger.error(f"Duffel flight search timed out after {self.timeout}s: {e}")
            raise DuffelServiceUnavailableError("Duffel flight search request timed out.")
        except httpx.RequestError as e:
            logger.error(f"Network error reaching Duffel flight search: {e}")
            raise DuffelServiceUnavailableError(f"Network communication failure reaching Duffel: {str(e)}")

        if not response.is_success:
            self._handle_http_error(response, "/air/offer_requests")

        try:
            res_json = response.json()
            data = res_json.get("data") or {}
            raw_offers = data.get("offers") or []
        except Exception as e:
            logger.error(f"Failed to parse Duffel flight response: {e}")
            raise DuffelValidationError("Duffel returned an unparseable JSON response.")

        normalized_offers: List[FlightOfferItem] = []
        for raw_off in raw_offers:
            normalized = self.normalize_flight_offer(raw_off, total_passengers)
            if normalized:
                normalized_offers.append(normalized)

        return FlightSearchResponse(
            provider="DUFFEL",
            total_offers=len(normalized_offers),
            query=request,
            offers=normalized_offers,
        )

    # --- HOTEL / ACCOMMODATION SEARCH ---

    def build_hotel_request_payload(self, request: HotelSearchRequest) -> Dict[str, Any]:
        """Constructs official Duffel Stays Search JSON body."""
        guests = [{"type": "adult"} for _ in range(request.guests)]
        return {
            "data": {
                "location": {
                    "geographic_coordinates": {
                        "latitude": float(request.latitude),
                        "longitude": float(request.longitude),
                    },
                    "radius": int(request.radius_km),
                },
                "check_in_date": str(request.check_in_date),
                "check_out_date": str(request.check_out_date),
                "rooms": int(request.rooms),
                "guests": guests,
            }
        }

    def normalize_hotel_offer(
        self,
        result: Dict[str, Any],
        request: HotelSearchRequest,
    ) -> List[HotelOfferItem]:
        """
        Normalizes a Duffel accommodation result with room rates into HotelOfferItems.
        Extracts verified pricing, cancellation policies, and coordinates.
        """
        acc = result.get("accommodation") or {}
        acc_name = acc.get("name") or "Accommodation"
        rating = acc.get("rating")

        # Location details
        loc = acc.get("location") or {}
        geo = loc.get("geographic_coordinates") or {}
        lat = geo.get("latitude")
        lon = geo.get("longitude")

        # Address formatting
        raw_addr = loc.get("address") or {}
        addr_parts = [
            raw_addr.get("line_one"),
            raw_addr.get("city_name"),
            raw_addr.get("postal_code"),
            raw_addr.get("country_code"),
        ]
        formatted_address = ", ".join(p for p in addr_parts if p) or None

        # Photos
        photos_list = [p.get("url") for p in (acc.get("photos") or []) if p.get("url")]

        rooms = result.get("rooms") or []
        items: List[HotelOfferItem] = []

        if rooms:
            for room in rooms:
                room_name = room.get("name")
                rates = room.get("rates") or []
                for rate in rates:
                    rate_id = rate.get("id") or result.get("id")
                    price_str = rate.get("total_amount") or result.get("cheapest_rate_total_amount")
                    currency = rate.get("total_currency") or result.get("cheapest_rate_currency") or "USD"

                    if not rate_id or price_str is None:
                        continue

                    try:
                        price = Decimal(str(price_str))
                    except Exception:
                        continue

                    # Cancellation policy extraction
                    cancellation_timeline = rate.get("cancellation_timeline") or []
                    cancel_policy = None
                    if cancellation_timeline:
                        first_cancel = cancellation_timeline[0]
                        before_dt = first_cancel.get("before")
                        refund = first_cancel.get("refund_amount")
                        if before_dt:
                            cancel_policy = f"Refund {refund} {currency} if cancelled before {before_dt}"
                    elif rate.get("conditions"):
                        cancel_policy = str(rate.get("conditions"))

                    # Expiration
                    expires_at = None
                    raw_exp = rate.get("expires_at")
                    if raw_exp:
                        try:
                            expires_at = datetime.fromisoformat(raw_exp.replace("Z", "+00:00"))
                        except Exception:
                            pass

                    items.append(
                        HotelOfferItem(
                            id=str(rate_id),
                            provider="DUFFEL",
                            provider_offer_id=str(rate_id),
                            accommodation_name=acc_name,
                            address=formatted_address,
                            latitude=float(lat) if lat is not None else None,
                            longitude=float(lon) if lon is not None else None,
                            rating=float(rating) if rating is not None else None,
                            room_name=room_name,
                            price=price,
                            currency=str(currency).upper(),
                            cancellation_policy=cancel_policy,
                            check_in_date=request.check_in_date,
                            check_out_date=request.check_out_date,
                            photos=photos_list,
                            expires_at=expires_at,
                            retrieved_at=datetime.utcnow(),
                        )
                    )

        # Fallback if no individual rates array but cheapest rate present
        if not items and result.get("cheapest_rate_total_amount"):
            acc_id = result.get("id") or acc.get("id")
            if acc_id:
                try:
                    price = Decimal(str(result.get("cheapest_rate_total_amount")))
                    items.append(
                        HotelOfferItem(
                            id=str(acc_id),
                            provider="DUFFEL",
                            provider_offer_id=str(acc_id),
                            accommodation_name=acc_name,
                            address=formatted_address,
                            latitude=float(lat) if lat is not None else None,
                            longitude=float(lon) if lon is not None else None,
                            rating=float(rating) if rating is not None else None,
                            room_name="Standard Room",
                            price=price,
                            currency=str(result.get("cheapest_rate_currency", "USD")).upper(),
                            cancellation_policy=None,
                            check_in_date=request.check_in_date,
                            check_out_date=request.check_out_date,
                            photos=photos_list,
                            expires_at=None,
                            retrieved_at=datetime.utcnow(),
                        )
                    )
                except Exception:
                    pass

        return items

    async def search_hotels(self, request: HotelSearchRequest) -> HotelSearchResponse:
        """
        Executes accommodation search via Duffel's Stays API (`POST /stays/search`).
        Returns normalized accommodation offers or raises a domain exception on failure.
        """
        headers = self._get_headers()
        payload = self.build_hotel_request_payload(request)
        url = f"{self.api_url}/stays/search"

        try:
            if self._custom_client:
                response = await self._custom_client.post(
                    url, json=payload, headers=headers, timeout=self.timeout
                )
            else:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload, headers=headers)
        except httpx.TimeoutException as e:
            logger.error(f"Duffel stays search timed out after {self.timeout}s: {e}")
            raise DuffelServiceUnavailableError("Duffel accommodation search request timed out.")
        except httpx.RequestError as e:
            logger.error(f"Network error reaching Duffel stays search: {e}")
            raise DuffelServiceUnavailableError(f"Network communication failure reaching Duffel: {str(e)}")

        if not response.is_success:
            self._handle_http_error(response, "/stays/search")

        try:
            res_json = response.json()
            data = res_json.get("data") or {}
            raw_results = data.get("results") or []
        except Exception as e:
            logger.error(f"Failed to parse Duffel stays response: {e}")
            raise DuffelValidationError("Duffel returned an unparseable JSON stays response.")

        normalized_offers: List[HotelOfferItem] = []
        for raw_res in raw_results:
            offers_for_acc = self.normalize_hotel_offer(raw_res, request)
            normalized_offers.extend(offers_for_acc)

        return HotelSearchResponse(
            provider="DUFFEL",
            total_offers=len(normalized_offers),
            query=request,
            offers=normalized_offers,
        )

