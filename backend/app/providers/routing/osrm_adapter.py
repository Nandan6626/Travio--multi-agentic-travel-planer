from abc import ABC, abstractmethod
from typing import List, Optional
import httpx
from app.schemas.routing import (
    Coordinate,
    RouteCalculateRequest,
    RouteCalculateResponse,
    RouteGeometry,
    RouteLeg,
)


class RoutingError(Exception):
    """Base exception for routing errors."""
    pass


class InvalidCoordinateError(RoutingError):
    """Raised when coordinates are out of geographical boundaries."""
    pass


class RouteNotFoundError(RoutingError):
    """Raised when no drivable/navigable path connects the coordinates."""
    pass


class RoutingServiceUnavailableError(RoutingError):
    """Raised when upstream routing service is down, timed out, or returning 5xx."""
    pass


class RoutingAdapterInterface(ABC):
    """Interface for routing engines (OSRM, GraphHopper, Google Routes, etc.)."""

    @abstractmethod
    async def calculate_route(
        self,
        request: RouteCalculateRequest,
        client: Optional[httpx.AsyncClient] = None,
    ) -> RouteCalculateResponse:
        pass


class OSRMAdapter(RoutingAdapterInterface):
    """OSRM (Open Source Routing Machine) implementation of RoutingAdapterInterface.
    
    Computes distances, estimated travel durations, and GeoJSON geometries.
    Explicitly indicates that estimates do not account for live traffic congestion.
    """

    def __init__(
        self,
        base_url: str = "https://router.project-osrm.org",
        timeout_seconds: float = 8.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.user_agent = "TravioAI-TripPlanner/1.0 (https://github.com/Nandan6626/Travio)"

    def _validate_coordinate(self, coord: Coordinate, label: str) -> None:
        if not (-90.0 <= coord.latitude <= 90.0):
            raise InvalidCoordinateError(f"{label} latitude {coord.latitude} is outside valid range [-90, 90].")
        if not (-180.0 <= coord.longitude <= 180.0):
            raise InvalidCoordinateError(f"{label} longitude {coord.longitude} is outside valid range [-180, 180].")

    async def calculate_route(
        self,
        request: RouteCalculateRequest,
        client: Optional[httpx.AsyncClient] = None,
    ) -> RouteCalculateResponse:
        # Validate coordinates
        self._validate_coordinate(request.origin, "Origin")
        self._validate_coordinate(request.destination, "Destination")
        if request.waypoints:
            for idx, wp in enumerate(request.waypoints):
                self._validate_coordinate(wp, f"Waypoint {idx + 1}")

        # Map profiles: driving, walking, cycling
        profile = request.profile.lower().strip()
        if profile not in ("driving", "walking", "cycling"):
            profile = "driving"

        # Build coordinates query: lon,lat;lon,lat;...
        coord_pairs = [f"{request.origin.longitude},{request.origin.latitude}"]
        if request.waypoints:
            for wp in request.waypoints:
                coord_pairs.append(f"{wp.longitude},{wp.latitude}")
        coord_pairs.append(f"{request.destination.longitude},{request.destination.latitude}")
        coords_str = ";".join(coord_pairs)

        url = f"{self.base_url}/route/v1/{profile}/{coords_str}"
        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "false",
        }
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }

        try:
            if client is not None:
                resp = await client.get(url, params=params, headers=headers, timeout=self.timeout_seconds)
                self._handle_response_errors(resp)
                data = resp.json()
            else:
                async with httpx.AsyncClient() as default_client:
                    resp = await default_client.get(url, params=params, headers=headers, timeout=self.timeout_seconds)
                    self._handle_response_errors(resp)
                    data = resp.json()
        except httpx.TimeoutException as e:
            raise RoutingServiceUnavailableError(f"OSRM routing request timed out: {e}") from e
        except httpx.RequestError as e:
            raise RoutingServiceUnavailableError(f"OSRM routing connection failed: {e}") from e

        code = data.get("code")
        if code != "Ok" or not data.get("routes"):
            raise RouteNotFoundError(f"OSRM could not calculate a valid route between coordinates ({code}).")

        primary_route = data["routes"][0]
        total_distance = float(primary_route.get("distance", 0.0))
        total_duration = float(primary_route.get("duration", 0.0))

        # Geometry
        raw_geom = primary_route.get("geometry", {})
        geometry = None
        if raw_geom and "coordinates" in raw_geom:
            geometry = RouteGeometry(
                type=raw_geom.get("type", "LineString"),
                coordinates=raw_geom["coordinates"],
            )

        # Legs breakdown
        legs: List[RouteLeg] = []
        for leg_data in primary_route.get("legs", []):
            legs.append(
                RouteLeg(
                    distance_meters=float(leg_data.get("distance", 0.0)),
                    duration_seconds=float(leg_data.get("duration", 0.0)),
                    summary=leg_data.get("summary", ""),
                )
            )

        return RouteCalculateResponse(
            distance_meters=round(total_distance, 1),
            distance_km=round(total_distance / 1000.0, 2),
            duration_seconds=round(total_duration, 1),
            duration_minutes=round(total_duration / 60.0, 1),
            is_traffic_adjusted=False,  # OSRM free public routing does not include real-time traffic
            geometry=geometry,
            legs=legs,
            profile=profile,
            provider="OSRM",
        )

    def _handle_response_errors(self, response: httpx.Response) -> None:
        if response.is_success:
            return

        status_code = response.status_code
        try:
            error_data = response.json()
            message = error_data.get("message") or response.text
        except Exception:
            message = response.text or f"HTTP {status_code}"

        if status_code in (400, 422):
            raise InvalidCoordinateError(f"Invalid routing parameters ({status_code}): {message}")
        elif status_code == 404:
            raise RouteNotFoundError(f"Route not found ({status_code}): {message}")
        elif status_code >= 500:
            raise RoutingServiceUnavailableError(f"OSRM routing service unavailable ({status_code}): {message}")
        else:
            raise RoutingError(f"Routing request failed with HTTP {status_code}: {message}")
