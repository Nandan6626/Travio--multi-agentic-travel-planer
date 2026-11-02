import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user_id
from app.models.trip import TripRole
from app.schemas.itinerary import (
    ItineraryItemUpdate,
    ItineraryItemRead,
)
from app.services.itinerary_service import ItineraryService

router = APIRouter()


@router.get(
    "/items/{item_id}",
    response_model=ItineraryItemRead,
    summary="Retrieve an activity",
    description="Returns activity details and linked place. Requires trip membership.",
)
async def get_item(
    item_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ItineraryItemRead:
    item, _ = await ItineraryService.get_permitted_item(
        db=db, item_id=item_id, user_id=user_id, min_role=TripRole.VIEWER
    )
    return ItineraryItemRead.model_validate(item)


@router.patch(
    "/items/{item_id}",
    response_model=ItineraryItemRead,
    summary="Update an activity",
    description="Updates activity properties. Validates schedule non-overlap. Requires OWNER or EDITOR role.",
)
async def update_item(
    item_id: uuid.UUID,
    data: ItineraryItemUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ItineraryItemRead:
    updated = await ItineraryService.update_item(
        db=db, item_id=item_id, user_id=user_id, data=data
    )
    return ItineraryItemRead.model_validate(updated)


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an activity",
    description="Deletes an activity item. Requires OWNER or EDITOR role.",
)
async def delete_item(
    item_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    await ItineraryService.delete_item(
        db=db, item_id=item_id, user_id=user_id
    )
    return None

