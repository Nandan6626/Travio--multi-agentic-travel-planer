import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user_id
from app.schemas.place import (
    PlaceCreate,
    PlaceRead,
    PlaceSearchResult,
)
from app.services.place_service import PlaceService

router = APIRouter()
place_service = PlaceService()


@router.get(
    "/search",
    response_model=List[PlaceSearchResult],
    summary="Search places and points of interest",
    description="Searches real places via Geoapify by destination text or coordinates, categories, and radius.",
)
async def search_places(
    text: Optional[str] = Query(None, description="City, address or POI keyword (e.g. 'Paris', 'Louvre')"),
    categories: str = Query("tourism.attraction,catering.restaurant,entertainment,leisure", description="Comma-separated Geoapify categories"),
    lat: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Center latitude coordinate"),
    lon: Optional[float] = Query(None, ge=-180.0, le=180.0, description="Center longitude coordinate"),
    radius_meters: int = Query(5000, ge=100, le=50000, description="Search radius in meters"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of results"),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> List[PlaceSearchResult]:
    return await place_service.search_places(
        db=db,
        text=text,
        categories=categories,
        lat=lat,
        lon=lon,
        radius_meters=radius_meters,
        limit=limit,
    )


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
    description="Retrieves a place by internal UUID or external Geoapify provider ID (automatically caching if external).",
)
async def get_place(
    place_id: str,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> PlaceRead:
    place = await place_service.get_or_cache_place(db=db, identifier=place_id)
    return PlaceRead.model_validate(place)
