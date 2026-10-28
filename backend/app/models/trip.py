import uuid
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import List, TYPE_CHECKING
from sqlalchemy import (
    String,
    Date,
    Numeric,
    Integer,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, TimestampMixin, GUID

if TYPE_CHECKING:
    from app.models.profile import Profile


class TripRole(str, Enum):
    OWNER = "OWNER"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"


class TripStatus(str, Enum):
    PLANNING = "PLANNING"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class Trip(Base, TimestampMixin):
    __tablename__ = "trips"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    destination: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_budget: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    traveler_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=TripStatus.PLANNING.value)

    # Relationships
    owner: Mapped["Profile"] = relationship("Profile", back_populates="owned_trips")
    members: Mapped[List["TripMember"]] = relationship(
        "TripMember",
        back_populates="trip",
        cascade="all, delete-orphan",
    )


class TripMember(Base, TimestampMixin):
    __tablename__ = "trip_members"
    __table_args__ = (
        UniqueConstraint("trip_id", "profile_id", name="uq_trip_member"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=TripRole.VIEWER.value)

    # Relationships
    trip: Mapped["Trip"] = relationship("Trip", back_populates="members")
    profile: Mapped["Profile"] = relationship("Profile", back_populates="memberships")
