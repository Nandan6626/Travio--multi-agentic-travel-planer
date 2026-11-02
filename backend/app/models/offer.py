import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from sqlalchemy import (
    String,
    Numeric,
    DateTime,
    ForeignKey,
    JSON,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, TimestampMixin, GUID

if TYPE_CHECKING:
    from app.models.trip import Trip


class SearchRecord(Base):
    __tablename__ = "search_records"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID,
        ForeignKey("trips.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    search_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # FLIGHT, HOTEL
    search_parameters: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    trip: Mapped[Optional["Trip"]] = relationship("Trip")
    offers: Mapped[List["TravelOffer"]] = relationship(
        "TravelOffer",
        back_populates="search_record",
        cascade="all, delete-orphan",
    )


class TravelOffer(Base, TimestampMixin):
    __tablename__ = "travel_offers"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    search_record_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID,
        ForeignKey("search_records.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    provider_name: Mapped[str] = mapped_column(String(50), nullable=False, default="DUFFEL")  # DUFFEL
    offer_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # FLIGHT, HOTEL
    provider_offer_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    verified_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    offer_details: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Relationships
    search_record: Mapped[Optional["SearchRecord"]] = relationship("SearchRecord", back_populates="offers")

