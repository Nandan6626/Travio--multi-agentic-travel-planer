import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user_id
from app.schemas.place import PlaceCreate, PlaceRead
from app.services.place_service import PlaceService

router = APIRouter()


@router.post(
    "",
    response_model=PlaceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a place with coordinates",
    description="Registers a place/venue with geographical coordinates (latitude and longitude).",
)
async def create_place(
    data: PlaceCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> PlaceRead:
    place = await PlaceService.create_place(db=db, data=data)
    return PlaceRead.model_validate(place)


@router.get(
    "/{place_id}",
    response_model=PlaceRead,
    summary="Retrieve place details",
    description="Retrieves a place and its geographical coordinates.",
)
async def get_place(
    place_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> PlaceRead:
    place = await PlaceService.get_place(db=db, place_id=place_id)
    return PlaceRead.model_validate(place)

