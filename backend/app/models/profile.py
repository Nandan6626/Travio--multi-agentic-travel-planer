import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, TimestampMixin, GUID

if TYPE_CHECKING:
    from app.models.trip import Trip, TripMember


class Profile(Base, TimestampMixin):
    __tablename__ = "profiles"

    # ID maps directly to Supabase auth.users UUID
    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Relationships
    owned_trips: Mapped[List["Trip"]] = relationship(
        "Trip",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    memberships: Mapped[List["TripMember"]] = relationship(
        "TripMember",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
