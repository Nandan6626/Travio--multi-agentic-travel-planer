import uuid
from typing import List, Tuple, Optional
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models.profile import Profile
from app.models.trip import Trip, TripMember, TripRole
from app.schemas.trip import TripCreate, TripUpdate


ROLE_HIERARCHY = {
    TripRole.VIEWER: 1,
    TripRole.EDITOR: 2,
    TripRole.OWNER: 3,
}


class TripService:
    @staticmethod
    async def get_or_create_profile(
        db: AsyncSession,
        user_id: uuid.UUID,
        email: str,
        full_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> Profile:
        """Finds existing profile or creates one for the verified user."""
        stmt = select(Profile).where(Profile.id == user_id)
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()

        if not profile:
            profile = Profile(
                id=user_id,
                email=email,
                full_name=full_name,
                avatar_url=avatar_url,
            )
            db.add(profile)
            await db.commit()
            await db.refresh(profile)
        elif full_name is not None or avatar_url is not None:
            if full_name is not None:
                profile.full_name = full_name
            if avatar_url is not None:
                profile.avatar_url = avatar_url
            await db.commit()
            await db.refresh(profile)

        return profile

    @staticmethod
    async def create_trip(
        db: AsyncSession,
        owner_id: uuid.UUID,
        data: TripCreate,
    ) -> Trip:
        """
        Creates a trip and an OWNER membership record in the same atomic transaction.
        """
        trip = Trip(
            owner_id=owner_id,
            title=data.title,
            destination=data.destination,
            start_date=data.start_date,
            end_date=data.end_date,
            total_budget=data.total_budget,
            currency=data.currency,
            traveler_count=data.traveler_count,
        )
        db.add(trip)
        await db.flush()  # Flush to generate trip.id

        # Insert corresponding OWNER member record
        owner_member = TripMember(
            trip_id=trip.id,
            profile_id=owner_id,
            role=TripRole.OWNER.value,
        )
        db.add(owner_member)
        await db.commit()

        # Reload with relationships
        stmt = (
            select(Trip)
            .options(selectinload(Trip.members).selectinload(TripMember.profile))
            .where(Trip.id == trip.id)
        )
        result = await db.execute(stmt)
        return result.scalar_one()

    @staticmethod
    async def list_trips(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> List[Tuple[Trip, TripRole]]:
        """
        Lists all trips the user owns or is a member of.
        Returns a list of tuples (Trip, user_role).
        """
        stmt = (
            select(Trip, TripMember.role)
            .join(TripMember, and_(TripMember.trip_id == Trip.id, TripMember.profile_id == user_id))
            .options(selectinload(Trip.members).selectinload(TripMember.profile))
            .order_by(Trip.start_date.asc())
        )
        result = await db.execute(stmt)
        rows = result.all()
        return [(row[0], TripRole(row[1])) for row in rows]

    @staticmethod
    async def get_permitted_trip(
        db: AsyncSession,
        trip_id: uuid.UUID,
        user_id: uuid.UUID,
        min_role: Optional[TripRole] = None,
    ) -> Tuple[Trip, TripRole]:
        """
        Retrieves a trip and enforces membership and role permissions.
        - Raises 404 if trip does not exist.
        - Raises 403 if user is not a member.
        - Raises 403 if user role does not satisfy min_role.
        """
        stmt = (
            select(Trip)
            .options(selectinload(Trip.members).selectinload(TripMember.profile))
            .where(Trip.id == trip_id)
        )
        result = await db.execute(stmt)
        trip = result.scalar_one_or_none()

        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found",
            )

        # Check membership
        member_stmt = select(TripMember.role).where(
            TripMember.trip_id == trip_id,
            TripMember.profile_id == user_id,
        )
        member_res = await db.execute(member_stmt)
        user_role_str = member_res.scalar_one_or_none()

        # Fallback check on authoritative owner_id
        if not user_role_str and trip.owner_id == user_id:
            user_role_str = TripRole.OWNER.value

        if not user_role_str:
            # Cross-user IDOR protection: return 403 Forbidden
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this trip",
            )

        user_role = TripRole(user_role_str)

        if min_role:
            if ROLE_HIERARCHY[user_role] < ROLE_HIERARCHY[min_role]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Action requires {min_role.value} permission, but you have {user_role.value}",
                )

        return trip, user_role

    @staticmethod
    async def update_trip(
        db: AsyncSession,
        trip: Trip,
        data: TripUpdate,
    ) -> Trip:
        """Applies updates to trip and persists changes."""
        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if hasattr(trip, key):
                setattr(trip, key, value)

        await db.commit()
        await db.refresh(trip)
        return trip

    @staticmethod
    async def delete_trip(
        db: AsyncSession,
        trip: Trip,
    ) -> None:
        """Deletes a trip (cascades to trip_members)."""
        await db.delete(trip)
        await db.commit()
