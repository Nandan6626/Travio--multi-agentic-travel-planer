import uuid
import datetime as dt
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator


class FlightSearchRequest(BaseModel):
    origin: str = Field(..., min_length=2, max_length=100, description="Origin airport IATA code or city")
    destination: str = Field(..., min_length=2, max_length=100, description="Destination airport IATA code or city")
    departure_date: dt.date = Field(..., description="Departure date (YYYY-MM-DD)")
    return_date: Optional[dt.date] = Field(None, description="Return date for round trips (YYYY-MM-DD)")
    adults: int = Field(default=1, ge=1, le=9, description="Number of adult passengers (18+)")
    children: int = Field(default=0, ge=0, le=8, description="Number of child passengers")
    cabin_class: str = Field(
        default="economy",
        description="Cabin class: economy, premium_economy, business, or first",
    )
    trip_id: Optional[uuid.UUID] = Field(None, description="Optional associated Trip UUID")

    @field_validator("cabin_class")
    @classmethod
    def validate_cabin_class(cls, v: str) -> str:
        clean = v.strip().lower()
        allowed = {"economy", "premium_economy", "business", "first"}
        if clean not in allowed:
            raise ValueError(f"Cabin class must be one of: {', '.join(sorted(allowed))}")
        return clean

    @model_validator(mode="after")
    def validate_dates(self) -> "FlightSearchRequest":
        if self.return_date and self.return_date < self.departure_date:
            raise ValueError("return_date cannot be earlier than departure_date")
        return self


class FlightOfferItem(BaseModel):
    id: str = Field(..., description="Unique offer identifier")
    provider: str = Field(default="DUFFEL", description="Upstream travel provider name")
    provider_offer_id: str = Field(..., description="Duffel offer ID (e.g. off_0000...)")
    airline_name: str = Field(..., description="Marketing carrier / airline name")
    airline_code: Optional[str] = Field(None, description="IATA 2-letter airline code")
    airline_logo_url: Optional[str] = Field(None, description="Airline logo symbol URL")
    price: Decimal = Field(..., ge=Decimal("0.00"), description="Total verified price from provider")
    currency: str = Field(..., min_length=3, max_length=3, description="ISO currency code")
    departure_time: dt.datetime = Field(..., description="Outbound flight departure timestamp")
    arrival_time: dt.datetime = Field(..., description="Outbound flight arrival timestamp")
    duration: str = Field(..., description="Human-readable flight duration (e.g. 7h 45m)")
    duration_minutes: int = Field(..., ge=0, description="Flight duration in minutes")
    stops: int = Field(default=0, ge=0, description="Total number of stops/connections")
    slices: List[Dict[str, Any]] = Field(default_factory=list, description="Raw slice flight segments")
    passengers_count: int = Field(default=1, ge=1, description="Total passenger count")
    expires_at: Optional[dt.datetime] = Field(None, description="Offer price validity expiration timestamp")
    retrieved_at: dt.datetime = Field(default_factory=lambda: dt.datetime.now(dt.timezone.utc), description="Retrieval timestamp")

    model_config = ConfigDict(from_attributes=True)


class FlightSearchResponse(BaseModel):
    provider: str = "DUFFEL"
    total_offers: int
    query: FlightSearchRequest
    offers: List[FlightOfferItem]


class HotelSearchRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Search center latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Search center longitude")
    radius_km: int = Field(default=20, ge=1, le=100, description="Search radius in kilometers (1-100)")
    check_in_date: dt.date = Field(..., description="Check-in date (YYYY-MM-DD)")
    check_out_date: dt.date = Field(..., description="Check-out date (YYYY-MM-DD)")
    rooms: int = Field(default=1, ge=1, le=9, description="Number of rooms requested")
    guests: int = Field(default=1, ge=1, le=18, description="Number of adult guests")
    trip_id: Optional[uuid.UUID] = Field(None, description="Optional associated Trip UUID")

    @model_validator(mode="after")
    def validate_dates(self) -> "HotelSearchRequest":
        if self.check_out_date <= self.check_in_date:
            raise ValueError("check_out_date must be later than check_in_date")
        return self


class HotelOfferItem(BaseModel):
    id: str = Field(..., description="Unique accommodation rate identifier")
    provider: str = Field(default="DUFFEL", description="Upstream travel provider name")
    provider_offer_id: str = Field(..., description="Duffel rate/accommodation ID")
    accommodation_name: str = Field(..., description="Hotel / accommodation property name")
    address: Optional[str] = Field(None, description="Street address")
    latitude: Optional[float] = Field(None, description="Geographic latitude")
    longitude: Optional[float] = Field(None, description="Geographic longitude")
    rating: Optional[float] = Field(None, description="Hotel star rating")
    room_name: Optional[str] = Field(None, description="Room category / rate description")
    price: Decimal = Field(..., ge=Decimal("0.00"), description="Total verified stay price")
    currency: str = Field(..., min_length=3, max_length=3, description="ISO currency code")
    cancellation_policy: Optional[str] = Field(None, description="Cancellation conditions summary")
    check_in_date: dt.date = Field(..., description="Check-in date")
    check_out_date: dt.date = Field(..., description="Check-out date")
    photos: List[str] = Field(default_factory=list, description="Property photo URLs")
    expires_at: Optional[dt.datetime] = Field(None, description="Offer price validity expiration timestamp")
    retrieved_at: dt.datetime = Field(default_factory=lambda: dt.datetime.now(dt.timezone.utc), description="Retrieval timestamp")

    model_config = ConfigDict(from_attributes=True)


class HotelSearchResponse(BaseModel):
    provider: str = "DUFFEL"
    total_offers: int
    query: HotelSearchRequest
    offers: List[HotelOfferItem]

