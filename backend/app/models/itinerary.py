import uuid
from datetime import date, time
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    String,
    Date,
    Time,
    Integer,
    Numeric,
    Text,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, TimestampMixin, GUID

if TYPE_CHECKING:
    from app.models.trip import Trip
    from app.models.place import Place


class ItineraryDay(Base, TimestampMixin):
    __tablename__ = "itinerary_days"
    __table_args__ = (
        UniqueConstraint("trip_id", "day_number", name="uq_trip_day_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    trip: Mapped["Trip"] = relationship("Trip", back_populates="days")
    items: Mapped[List["ItineraryItem"]] = relationship(
        "ItineraryItem",
        back_populates="day",
        cascade="all, delete-orphan",
        order_by="ItineraryItem.order_index",
    )


class ItineraryItem(Base, TimestampMixin):
    __tablename__ = "itinerary_items"
    __table_args__ = (
        UniqueConstraint("day_id", "order_index", name="uq_day_item_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    day_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("itinerary_days.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    place_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID,
        ForeignKey("places.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    activity_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="sightseeing")
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    # Relationships
    day: Mapped["ItineraryDay"] = relationship("ItineraryDay", back_populates="items")
    place: Mapped[Optional["Place"]] = relationship("Place", back_populates="itinerary_items")

