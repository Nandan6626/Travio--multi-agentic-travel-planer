import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ProfileBase(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = Field(None, max_length=1024)


class ProfileSync(ProfileBase):
    pass


class ProfileRead(ProfileBase):
    id: uuid.UUID
    email: str = Field(..., max_length=255, description="User email address")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
