from typing import List, Optional
from pydantic import BaseModel, Field


class Coordinate(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")
    name: Optional[str] = Field(None, description="Optional waypoint or place name")


class RouteCalculateRequest(BaseModel):
    origin: Coordinate = Field(..., description="Starting location coordinate")
    destination: Coordinate = Field(..., description="Ending location coordinate")
    waypoints: Optional[List[Coordinate]] = Field(default_factory=list, description="Intermediate stops in order")
    profile: str = Field(default="driving", description="Routing profile: driving, walking, or cycling")


class RouteGeometry(BaseModel):
    type: str = Field(default="LineString", description="GeoJSON geometry type")
    coordinates: List[List[float]] = Field(..., description="Array of [longitude, latitude] coordinate pairs")


class RouteLeg(BaseModel):
    distance_meters: float = Field(..., description="Leg distance in meters")
    duration_seconds: float = Field(..., description="Estimated travel duration in seconds")
    summary: Optional[str] = Field(default="", description="Summary of roadways traversed")


class RouteCalculateResponse(BaseModel):
    distance_meters: float = Field(..., description="Total route distance in meters")
    distance_km: float = Field(..., description="Total route distance rounded to kilometers")
    duration_seconds: float = Field(..., description="Estimated travel duration in seconds")
    duration_minutes: float = Field(..., description="Estimated travel duration in minutes")
    is_traffic_adjusted: bool = Field(
        default=False,
        description="False for free-flow / speed-limit heuristic estimates; True only when real-time traffic is integrated",
    )
    geometry: Optional[RouteGeometry] = Field(None, description="Route line coordinates in GeoJSON format")
    legs: List[RouteLeg] = Field(default_factory=list, description="Detailed per-segment distance and duration breakdown")
    profile: str = Field(default="driving", description="Profile used for routing calculation")
    provider: str = Field(default="OSRM", description="Routing data provider name")
