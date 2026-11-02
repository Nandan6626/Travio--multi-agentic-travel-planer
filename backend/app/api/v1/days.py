import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user_id
from app.models.trip import TripRole
from app.schemas.itinerary import (
    ItineraryDayCreate,
    ItineraryDayUpdate,
    ItineraryDayRead,
    ItineraryItemCreate,
    ItineraryItemRead,
    ItineraryItemReorderRequest,
)
from app.services.itinerary_service import ItineraryService

router = APIRouter()


# --- Itinerary Days Endpoints ---

@router.post(
    "/trips/{trip_id}/days",
    response_model=ItineraryDayRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an itinerary day",
    description="Adds an itinerary day to the specified trip. Requires OWNER or EDITOR role.",
)
async def create_day(
    trip_id: uuid.UUID,
    data: ItineraryDayCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ItineraryDayRead:
    day = await ItineraryService.create_day(
        db=db, trip_id=trip_id, user_id=user_id, data=data
    )
    return ItineraryDayRead.model_validate(day)


@router.get(
    "/trips/{trip_id}/days",
    response_model=List[ItineraryDayRead],
    summary="List all days for a trip",
    description="Returns all itinerary days ordered by day number. Requires trip membership.",
)
async def list_days(
    trip_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> List[ItineraryDayRead]:
    days = await ItineraryService.list_days(
        db=db, trip_id=trip_id, user_id=user_id
    )
    return [ItineraryDayRead.model_validate(d) for d in days]


@router.get(
    "/days/{day_id}",
    response_model=ItineraryDayRead,
    summary="Retrieve an itinerary day",
    description="Returns day details and associated activities. Requires trip membership.",
)
async def get_day(
    day_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ItineraryDayRead:
    day, _ = await ItineraryService.get_permitted_day(
        db=db, day_id=day_id, user_id=user_id, min_role=TripRole.VIEWER
    )
    return ItineraryDayRead.model_validate(day)


@router.patch(
    "/days/{day_id}",
    response_model=ItineraryDayRead,
    summary="Update an itinerary day",
    description="Updates day properties. Requires OWNER or EDITOR role.",
)
async def update_day(
    day_id: uuid.UUID,
    data: ItineraryDayUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ItineraryDayRead:
    updated = await ItineraryService.update_day(
        db=db, day_id=day_id, user_id=user_id, data=data
    )
    return ItineraryDayRead.model_validate(updated)


@router.delete(
    "/days/{day_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an itinerary day",
    description="Deletes an itinerary day and all child activities. Requires OWNER or EDITOR role.",
)
async def delete_day(
    day_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    await ItineraryService.delete_day(
        db=db, day_id=day_id, user_id=user_id
    )
    return None


# --- Day-Scoped Activities Endpoints ---

@router.post(
    "/days/{day_id}/items",
    response_model=ItineraryItemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add an activity to an itinerary day",
    description="Creates a new activity for the day. Validates non-overlapping schedule. Requires OWNER or EDITOR role.",
)
async def add_item(
    day_id: uuid.UUID,
    data: ItineraryItemCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ItineraryItemRead:
    item = await ItineraryService.create_item(
        db=db, day_id=day_id, user_id=user_id, data=data
    )
    return ItineraryItemRead.model_validate(item)


@router.get(
    "/days/{day_id}/items",
    response_model=List[ItineraryItemRead],
    summary="List activities for an itinerary day",
    description="Lists all activities for the day ordered chronologically. Requires trip membership.",
)
async def list_items(
    day_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> List[ItineraryItemRead]:
    items = await ItineraryService.list_items(
        db=db, day_id=day_id, user_id=user_id
    )
    return [ItineraryItemRead.model_validate(item) for item in items]


@router.patch(
    "/days/{day_id}/items/reorder",
    response_model=List[ItineraryItemRead],
    summary="Reorder activities in an itinerary day",
    description="Atomically reorders all activities for the day in a single transaction. Requires OWNER or EDITOR role.",
)
async def reorder_items(
    day_id: uuid.UUID,
    data: ItineraryItemReorderRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> List[ItineraryItemRead]:
    reordered = await ItineraryService.reorder_items(
        db=db, day_id=day_id, user_id=user_id, item_ids=data.item_ids
    )
    return [ItineraryItemRead.model_validate(item) for item in reordered]

