import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator
from app.models.trip import TripRole, TripStatus


class TripBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Trip title")
    destination: str = Field(..., min_length=1, max_length=255, description="Destination city/country")
    start_date: date = Field(..., description="Trip start date (YYYY-MM-DD)")
    end_date: date = Field(..., description="Trip end date (YYYY-MM-DD)")
    total_budget: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"), description="Total budget limit")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="ISO currency code")
    traveler_count: int = Field(default=1, ge=1, le=100, description="Number of travelers")

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        clean = v.strip().upper()
        if not clean.isalpha() or len(clean) != 3:
            raise ValueError("Currency must be a 3-letter ISO code (e.g. USD, EUR, INR)")
        return clean

    @model_validator(mode="after")
    def validate_dates(self) -> "TripBase":
        if self.end_date < self.start_date:
            raise ValueError("Trip end_date cannot be earlier than start_date")
        return self


class TripCreate(TripBase):
    pass


class TripUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    destination: Optional[str] = Field(None, min_length=1, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_budget: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    traveler_count: Optional[int] = Field(None, ge=1, le=100)
    status: Optional[TripStatus] = None

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip().upper()
            if not clean.isalpha() or len(clean) != 3:
                raise ValueError("Currency must be a 3-letter ISO code")
            return clean
        return v

    @model_validator(mode="after")
    def validate_dates(self) -> "TripUpdate":
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("Trip end_date cannot be earlier than start_date")
        return self


class TripMemberRead(BaseModel):
    id: uuid.UUID
    trip_id: uuid.UUID
    profile_id: uuid.UUID
    role: TripRole
    created_at: datetime
    email: Optional[str] = None
    full_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TripRead(TripBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    status: TripStatus
    created_at: datetime
    updated_at: datetime
    user_role: Optional[TripRole] = None
    members: Optional[List[TripMemberRead]] = None

    model_config = ConfigDict(from_attributes=True)


class TripListResponse(BaseModel):
    trips: List[TripRead]
    total: int
