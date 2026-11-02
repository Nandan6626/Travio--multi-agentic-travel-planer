import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


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

