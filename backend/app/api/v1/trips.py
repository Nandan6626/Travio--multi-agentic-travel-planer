import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import (
    get_db,
    get_current_user_id,
    get_current_profile,
    require_trip_role,
)
from app.models.profile import Profile
from app.models.trip import Trip, TripRole
from app.schemas.trip import (
    TripCreate,
    TripUpdate,
    TripRead,
    TripMemberRead,
    TripListResponse,
)
from app.services.trip_service import TripService

router = APIRouter()


@router.post(
    "",
    response_model=TripRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new trip",
    description="Creates a trip record with the authenticated user as owner, adding an OWNER member record in the same transaction.",
)
async def create_trip(
    data: TripCreate,
    current_profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
) -> TripRead:
    trip = await TripService.create_trip(
        db=db,
        owner_id=current_profile.id,
        data=data,
    )
    # Serialize members
    members_data = [
        TripMemberRead(
            id=m.id,
            trip_id=m.trip_id,
            profile_id=m.profile_id,
            role=TripRole(m.role),
            created_at=m.created_at,
            email=m.profile.email if m.profile else None,
            full_name=m.profile.full_name if m.profile else None,
        )
        for m in trip.members
    ]
    trip_read = TripRead.model_validate(trip)
    trip_read.user_role = TripRole.OWNER
    trip_read.members = members_data
    return trip_read


@router.get(
    "",
    response_model=TripListResponse,
    summary="List accessible trips",
    description="Returns all trips the authenticated user owns or participates in as a member.",
)
async def list_trips(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> TripListResponse:
    trips_with_roles = await TripService.list_trips(db=db, user_id=user_id)
    items: List[TripRead] = []

    for trip, role in trips_with_roles:
        members_data = [
            TripMemberRead(
                id=m.id,
                trip_id=m.trip_id,
                profile_id=m.profile_id,
                role=TripRole(m.role),
                created_at=m.created_at,
                email=m.profile.email if m.profile else None,
                full_name=m.profile.full_name if m.profile else None,
            )
            for m in trip.members
        ]
        tr = TripRead.model_validate(trip)
        tr.user_role = role
        tr.members = members_data
        items.append(tr)

    return TripListResponse(trips=items, total=len(items))


@router.get(
    "/{trip_id}",
    response_model=TripRead,
    summary="Get trip details",
    description="Retrieves a specific trip if the user is OWNER, EDITOR, or VIEWER. Returns 403 otherwise.",
)
async def get_trip(
    trip_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> TripRead:
    trip, role = await TripService.get_permitted_trip(
        db=db,
        trip_id=trip_id,
        user_id=user_id,
        min_role=TripRole.VIEWER,
    )
    members_data = [
        TripMemberRead(
            id=m.id,
            trip_id=m.trip_id,
            profile_id=m.profile_id,
            role=TripRole(m.role),
            created_at=m.created_at,
            email=m.profile.email if m.profile else None,
            full_name=m.profile.full_name if m.profile else None,
        )
        for m in trip.members
    ]
    tr = TripRead.model_validate(trip)
    tr.user_role = role
    tr.members = members_data
    return tr


@router.patch(
    "/{trip_id}",
    response_model=TripRead,
    summary="Update trip details",
    description="Updates trip properties. Requires OWNER or EDITOR role. VIEWER role receives 403.",
)
async def update_trip(
    trip_id: uuid.UUID,
    data: TripUpdate,
    trip: Trip = Depends(require_trip_role(TripRole.EDITOR)),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> TripRead:
    updated = await TripService.update_trip(db=db, trip=trip, data=data)
    _, role = await TripService.get_permitted_trip(db=db, trip_id=trip_id, user_id=user_id)
    tr = TripRead.model_validate(updated)
    tr.user_role = role
    return tr


@router.delete(
    "/{trip_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a trip",
    description="Deletes a trip. Strictly permitted only for the trip OWNER. Non-owners receive 403.",
)
async def delete_trip(
    trip_id: uuid.UUID,
    trip: Trip = Depends(require_trip_role(TripRole.OWNER)),
    db: AsyncSession = Depends(get_db),
) -> None:
    await TripService.delete_trip(db=db, trip=trip)
    return None
