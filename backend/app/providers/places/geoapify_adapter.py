import httpx
from typing import List, Optional, Dict, Any
from app.core.config import settings
from app.core.logging import logger
from app.schemas.place import PlaceSearchResult, DestinationSearchResult


class GeoapifyError(Exception):
    """Base exception for Geoapify provider errors."""
    pass


class GeoapifyAuthenticationError(GeoapifyError):
    """Raised when Geoapify API key is missing or rejected (401/403)."""
    pass


class GeoapifyRateLimitError(GeoapifyError):
    """Raised when Geoapify daily or burst rate limits are exceeded (429)."""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class GeoapifyServiceUnavailableError(GeoapifyError):
    """Raised when Geoapify service is unreachable, timed out, or returning 5xx."""
    pass


class GeoapifyValidationError(GeoapifyError):
    """Raised when Geoapify rejects query parameters (400/422)."""
    pass


class GeoapifyAdapter:
    """Production adapter for Geoapify Places and Geocoding APIs.
    
    Handles geocoding searches, category-based POI searches, place details,
    response normalization, and resilient error translation.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.geoapify.com",
        timeout_seconds: float = 8.0,
    ):
        self.api_key = api_key or settings.GEOAPIFY_API_KEY
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _ensure_api_key(self) -> str:
        if not self.api_key or not self.api_key.strip():
            raise GeoapifyAuthenticationError(
                "Geoapify API key is not configured. Set GEOAPIFY_API_KEY in backend/.env."
            )
        return self.api_key.strip()

    def _handle_response_errors(self, response: httpx.Response) -> None:
        if response.is_success:
            return

        status_code = response.status_code
        try:
            error_json = response.json()
            message = error_json.get("message") or error_json.get("error") or response.text
        except Exception:
            message = response.text or f"HTTP {status_code}"

        if status_code in (401, 403):
            raise GeoapifyAuthenticationError(f"Geoapify authentication failed ({status_code}): {message}")
        elif status_code == 429:
            retry_after_hdr = response.headers.get("Retry-After")
            retry_after = int(retry_after_hdr) if retry_after_hdr and retry_after_hdr.isdigit() else 60
            raise GeoapifyRateLimitError(f"Geoapify rate limit reached: {message}", retry_after=retry_after)
        elif status_code in (400, 422):
            raise GeoapifyValidationError(f"Geoapify rejected parameters ({status_code}): {message}")
        elif status_code >= 500:
            raise GeoapifyServiceUnavailableError(f"Geoapify service unavailable ({status_code}): {message}")
        else:
            raise GeoapifyError(f"Geoapify request failed with HTTP {status_code}: {message}")

    async def search_destination(
        self,
        query: str,
        limit: int = 5,
        client: Optional[httpx.AsyncClient] = None,
    ) -> List[DestinationSearchResult]:
        """Geocodes a destination text query (e.g. 'Paris', 'Tokyo') into coordinates."""
        key = self._ensure_api_key()
        if not query or not query.strip():
            return []

        url = f"{self.base_url}/v1/geocode/search"
        params = {
            "text": query.strip(),
            "limit": min(limit, 20),
            "apiKey": key,
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
            raise GeoapifyServiceUnavailableError(f"Geoapify destination geocoding timed out: {e}") from e
        except httpx.RequestError as e:
            raise GeoapifyServiceUnavailableError(f"Geoapify connection failed: {e}") from e

        results: List[DestinationSearchResult] = []
        features = data.get("features", [])
        for feat in features:
            props = feat.get("properties", {})
            lon = props.get("lon")
            lat = props.get("lat")
            if lat is None or lon is None:
                continue

            name = props.get("name") or props.get("city") or props.get("formatted") or query
            formatted = props.get("formatted") or name
            country = props.get("country")
            country_code = props.get("country_code")
            place_id = props.get("place_id")

            results.append(
                DestinationSearchResult(
                    name=name,
                    formatted_address=formatted,
                    country=country,
                    country_code=country_code.upper() if country_code else None,
                    latitude=float(lat),
                    longitude=float(lon),
                    place_id=place_id,
                )
            )

        return results

    async def search_places(
        self,
        lat: float,
        lon: float,
        categories: str = "tourism.attraction,catering.restaurant",
        radius_meters: int = 5000,
        limit: int = 20,
        name: Optional[str] = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> List[PlaceSearchResult]:
        """Searches points of interest by category and bounding circular radius."""
        key = self._ensure_api_key()
        url = f"{self.base_url}/v2/places"
        params: Dict[str, Any] = {
            "categories": categories,
            "filter": f"circle:{lon},{lat},{radius_meters}",
            "bias": f"proximity:{lon},{lat}",
            "limit": min(limit, 50),
            "apiKey": key,
        }
        if name and name.strip():
            params["name"] = name.strip()

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
            raise GeoapifyServiceUnavailableError(f"Geoapify places search timed out: {e}") from e
        except httpx.RequestError as e:
            raise GeoapifyServiceUnavailableError(f"Geoapify connection failed: {e}") from e

        results: List[PlaceSearchResult] = []
        features = data.get("features", [])
        for feat in features:
            props = feat.get("properties", {})
            place_id = props.get("place_id")
            plat = props.get("lat")
            plon = props.get("lon")
            if not place_id or plat is None or plon is None:
                continue

            name_val = props.get("name") or props.get("address_line1") or "Unnamed Place"
            formatted_address = props.get("formatted") or f"{props.get('address_line1', '')}, {props.get('address_line2', '')}".strip(", ")
            cats = props.get("categories", [])
            primary_cat = cats[0] if cats else "attraction"

            # Check ratings and opening hours strictly if supplied by provider
            rating = None
            if "rating" in props and isinstance(props["rating"], (int, float)):
                rating = float(props["rating"])
            elif "user_ratings_total" in props and "rating" in props:
                rating = float(props["rating"])

            opening_hours = props.get("opening_hours")
            website = props.get("website") or props.get("datasource", {}).get("raw", {}).get("website")

            results.append(
                PlaceSearchResult(
                    provider_id=place_id,
                    name=name_val,
                    address=formatted_address or None,
                    latitude=float(plat),
                    longitude=float(plon),
                    category=primary_cat,
                    categories=cats,
                    rating=rating,
                    opening_hours=opening_hours,
                    website=website,
                    is_cached=False,
                )
            )

        return results

    async def get_place_details(
        self,
        place_id: str,
        client: Optional[httpx.AsyncClient] = None,
    ) -> Optional[PlaceSearchResult]:
        """Retrieves verified place details for a given Geoapify place_id."""
        key = self._ensure_api_key()
        if not place_id:
            return None

        url = f"{self.base_url}/v2/place-details"
        params = {
            "id": place_id,
            "apiKey": key,
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
            raise GeoapifyServiceUnavailableError(f"Geoapify place details timed out: {e}") from e
        except httpx.RequestError as e:
            raise GeoapifyServiceUnavailableError(f"Geoapify connection failed: {e}") from e

        features = data.get("features", [])
        if not features:
            return None

        props = features[0].get("properties", {})
        plat = props.get("lat")
        plon = props.get("lon")
        if plat is None or plon is None:
            return None

        name_val = props.get("name") or props.get("address_line1") or "Unnamed Place"
        formatted_address = props.get("formatted") or f"{props.get('address_line1', '')}, {props.get('address_line2', '')}".strip(", ")
        cats = props.get("categories", [])
        primary_cat = cats[0] if cats else "attraction"

        rating = None
        if "rating" in props and isinstance(props["rating"], (int, float)):
            rating = float(props["rating"])

        opening_hours = props.get("opening_hours")
        website = props.get("website") or props.get("datasource", {}).get("raw", {}).get("website")

        return PlaceSearchResult(
            provider_id=place_id,
            name=name_val,
            address=formatted_address or None,
            latitude=float(plat),
            longitude=float(plon),
            category=primary_cat,
            categories=cats,
            rating=rating,
            opening_hours=opening_hours,
            website=website,
            is_cached=False,
        )
