import uuid
import datetime as dt
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator
from app.schemas.place import PlaceRead


class ItineraryDayBase(BaseModel):
    day_number: int = Field(..., ge=1, description="Sequential day number (1, 2, ...)")
    date: dt.date = Field(..., description="Calendar date of this itinerary day")
    title: str = Field(..., min_length=1, max_length=255, description="Day title or theme")
    notes: Optional[str] = Field(None, max_length=2000, description="Notes, reminders, packing hints")


class ItineraryDayCreate(ItineraryDayBase):
    pass


class ItineraryDayUpdate(BaseModel):
    day_number: Optional[int] = Field(None, ge=1)
    date: Optional[dt.date] = None
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    notes: Optional[str] = Field(None, max_length=2000)


class ItineraryItemBase(BaseModel):
    place_id: Optional[uuid.UUID] = Field(None, description="Linked place ID")
    activity_name: str = Field(..., min_length=1, max_length=255, description="Name of the activity")
    description: Optional[str] = Field(None, max_length=2000, description="Activity description")
    category: str = Field(default="sightseeing", max_length=100, description="Category (sightseeing, dining, etc.)")
    start_time: dt.time = Field(..., description="Start time (HH:MM:SS)")
    end_time: dt.time = Field(..., description="End time (HH:MM:SS)")
    order_index: Optional[int] = Field(None, ge=0, description="Position order in the day schedule")
    estimated_cost: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"), description="Estimated cost")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="Currency code")

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        clean = v.strip().upper()
        if not clean.isalpha() or len(clean) != 3:
            raise ValueError("Currency must be a 3-letter ISO code (e.g. USD, EUR, INR)")
        return clean

    @model_validator(mode="after")
    def validate_time_sequence(self) -> "ItineraryItemBase":
        if self.end_time <= self.start_time:
            raise ValueError("Activity end_time must be later than start_time")
        return self


class ItineraryItemCreate(ItineraryItemBase):
    pass


class ItineraryItemUpdate(BaseModel):
    place_id: Optional[uuid.UUID] = None
    activity_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = Field(None, max_length=100)
    start_time: Optional[dt.time] = None
    end_time: Optional[dt.time] = None
    order_index: Optional[int] = Field(None, ge=0)
    estimated_cost: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    currency: Optional[str] = Field(None, min_length=3, max_length=3)

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
    def validate_time_sequence(self) -> "ItineraryItemUpdate":
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError("Activity end_time must be later than start_time")
        return self


class ItineraryItemRead(BaseModel):
    id: uuid.UUID
    day_id: uuid.UUID
    place_id: Optional[uuid.UUID] = None
    activity_name: str
    description: Optional[str] = None
    category: str
    start_time: dt.time
    end_time: dt.time
    duration_minutes: int
    order_index: int
    estimated_cost: Decimal
    currency: str
    place: Optional[PlaceRead] = None
    created_at: dt.datetime
    updated_at: dt.datetime

    model_config = ConfigDict(from_attributes=True)


class ItineraryItemReorderRequest(BaseModel):
    item_ids: List[uuid.UUID] = Field(..., min_length=1, description="List of item IDs in desired chronological order")


class ItineraryDayRead(ItineraryDayBase):
    id: uuid.UUID
    trip_id: uuid.UUID
    items: List[ItineraryItemRead] = []
    created_at: dt.datetime
    updated_at: dt.datetime

    model_config = ConfigDict(from_attributes=True)
