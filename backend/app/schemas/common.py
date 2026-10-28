from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="API operational status")
    environment: str = Field(..., description="Current running environment")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Server UTC timestamp")
    services: Dict[str, str] = Field(
        default_factory=lambda: {"api": "operational", "database": "configured"},
        description="Subsystem health status map",
    )


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Detailed error description")
    code: Optional[str] = Field(None, description="Optional error code")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
