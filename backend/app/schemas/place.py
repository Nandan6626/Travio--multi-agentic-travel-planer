import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field


class PlaceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Place or venue name")
    provider_id: Optional[str] = Field(None, max_length=255, description="External provider identifier")
    address: Optional[str] = Field(None, max_length=500, description="Full street address")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude coordinate (-90 to 90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude coordinate (-180 to 180)")
    category: str = Field(default="attraction", max_length=100, description="Place category")
    rating: Optional[float] = Field(None, ge=0.0, le=5.0, description="Rating from 0.0 to 5.0")
    opening_hours: Optional[Dict[str, Any]] = Field(None, description="Opening hours structure")


class PlaceCreate(PlaceBase):
    pass


class PlaceRead(PlaceBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlaceSearchResult(BaseModel):
    provider_id: str = Field(..., description="External Geoapify place identifier")
    name: str = Field(..., description="Place name")
    address: Optional[str] = Field(None, description="Formatted address")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    category: str = Field(default="attraction", description="Primary category")
    categories: List[str] = Field(default_factory=list, description="All tagged categories")
    rating: Optional[float] = Field(None, description="User rating if supplied by provider")
    opening_hours: Optional[Dict[str, Any]] = Field(None, description="Opening hours structure")
    website: Optional[str] = Field(None, description="Official website URL")
    is_cached: bool = Field(default=False, description="Whether this place is already cached in local database")
    cached_place_id: Optional[uuid.UUID] = Field(None, description="Internal Place UUID if already cached")


class DestinationSearchResult(BaseModel):
    name: str = Field(..., description="City or destination name")
    formatted_address: str = Field(..., description="Formatted location string")
    country: Optional[str] = Field(None, description="Country name")
    country_code: Optional[str] = Field(None, description="ISO two-letter country code")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    place_id: Optional[str] = Field(None, description="External provider place ID")
