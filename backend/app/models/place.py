import uuid
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from sqlalchemy import String, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, TimestampMixin, GUID

if TYPE_CHECKING:
    from app.models.itinerary import ItineraryItem


class Place(Base, TimestampMixin):
    __tablename__ = "places"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    provider_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="attraction")
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    opening_hours: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    itinerary_items: Mapped[List["ItineraryItem"]] = relationship(
        "ItineraryItem",
        back_populates="place",
    )

